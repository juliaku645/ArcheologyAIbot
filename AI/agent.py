"""
Основной модуль агента для анализа изображений с использованием RAG системы.
"""
import os
import base64
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from database import ImageDatabase
from vector_db import VectorDatabase


# Загружаем переменные окружения
load_dotenv()


class Agent:
    """Класс агента для анализа изображений с использованием RAG системы."""
    
    def __init__(self):
        """Инициализация агента."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o")
        self.is_test = os.getenv("IS_TEST", "False").lower() == "true"
        self.system_prompt = os.getenv("SYSTEM_PROMPT", 
            "Ты полезный ассистент, который анализирует изображения археологических артефактов. "
            "Используй информацию из базы данных для более точного описания. Будь краток и информативен.")
        
        # Инициализируем базы данных
        self.db = ImageDatabase()
        self.vector_db = VectorDatabase()
        
        # Инициализируем LLM, если есть API ключ
        if self.openai_api_key:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.openai_api_key,
                max_tokens=1024
            )
        else:
            self.llm = None
    
    async def _process_image_with_llm(self, image_bytes: bytes, system_prompt: str, 
                                     user_prompt: str, context: list = None) -> str:
        """
        Обработать изображение с помощью языковой модели.
        
        Args:
            image_bytes: Байты изображения
            system_prompt: Системный промпт для LLM
            user_prompt: Пользовательский промпт
            context: Контекст разговора (список сообщений)
            
        Returns:
            Ответ от LLM
        """
        if not self.llm:
            raise ValueError("LLM не доступна (нет API ключа)")
        
        # Кодируем изображение в base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Формируем контент сообщения
        content = [
            {
                "type": "text",
                "text": user_prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]
        
        # Формируем сообщения
        messages = [
            SystemMessage(content=system_prompt)
        ]
        
        # Добавляем контекст, если есть
        if context:
            for item in context:
                if item["role"] == "user":
                    messages.append(HumanMessage(content=item["content"]))
                elif item["role"] == "assistant":
                    messages.append(SystemMessage(content=item["content"]))
        
        messages.append(HumanMessage(content=content))
        
        # Вызываем модель
        result = await self.llm.ainvoke(messages)
        return result.content
    
    def _get_description_for_image_test(self, image_bytes: bytes, user_context: str = None) -> str:
        """
        Тестовая версия метода get_description_for_image.
        
        Args:
            image_bytes: Байты изображения
            user_context: Пользовательский контекст
            
        Returns:
            Тестовое описание
        """
        print(f"Тестовый режим: изображение получено ({len(image_bytes)} байт), контекст: {user_context}")
        return "Очень красивая картинка (тестовый режим)"
    
    async def _get_description_for_image(self, image_bytes: bytes, user_context: str = None) -> str:
        """
        Получить описание изображения с использованием RAG системы.
        
        Выполняет следующую цепочку действий:
        1. По изображению в векторной БД находятся 3 похожих изображения
        2. По их hash в БД sqlite производится поиск описаний этих изображений
        3. Собранная информация отправляется в LLM для определения того, что находится на изображении
        
        Args:
            image_bytes: Байты изображения
            user_context: Пользовательский контекст (опционально)
            
        Returns:
            Описание изображения от LLM
        """
        # Шаг 1: Поиск похожих изображений в векторной БД
        print("🔍 Поиск похожих изображений в векторной БД...")
        similar_hashes = self.vector_db.search_similar(image_bytes, top_k=3)
        
        if not similar_hashes:
            print("⚠️ Похожие изображения не найдены в базе данных")
            similar_descriptions = []
        else:
            print(f"✅ Найдено {len(similar_hashes)} похожих изображений")
            
            # Шаг 2: Поиск описаний по hash в SQLite
            print("🔍 Поиск описаний в SQLite...")
            similar_descriptions = await self.db.get_descriptions_by_hashes(similar_hashes)
            print(f"✅ Найдено {len(similar_descriptions)} описаний")
        
        # Шаг 3: Формирование контекста для LLM
        context_text = ""
        if similar_descriptions:
            context_text = "Похожие описания из базы данных:\n"
            for i, desc in enumerate(similar_descriptions, 1):
                context_text += f"{i}. {desc}\n"
        
        # Формируем промпт для LLM
        user_prompt = f"Проанализируй это изображение и опиши, что на нем находится."
        if user_context:
            user_prompt += f"\n\nКонтекст пользователя: {user_context}"
        if context_text:
            user_prompt += f"\n\n{context_text}\nИспользуй эту информацию для более точного описания."
        
        # Шаг 4: Отправка в LLM
        print("🤖 Отправка запроса в LLM...")
        try:
            response = await self._process_image_with_llm(
                image_bytes=image_bytes,
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                context=None
            )
            print("✅ Получен ответ от LLM")
            return response
        except Exception as e:
            print(f"❌ Ошибка при обращении к LLM: {e}")
            raise
    
    async def get_description_for_image(self, image_bytes: bytes, user_context: str = None) -> str:
        """
        Публичный метод для получения описания изображения.
        
        Args:
            image_bytes: Байты изображения
            user_context: Пользовательский контекст (опционально)
            
        Returns:
            Описание изображения
        """
        if self.is_test:
            return self._get_description_for_image_test(image_bytes, user_context)
        else:
            return await self._get_description_for_image(image_bytes, user_context)


# Глобальный экземпляр агента для обратной совместимости
_agent_instance = None


def get_agent() -> Agent:
    """Получить глобальный экземпляр агента."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = Agent()
    return _agent_instance


async def get_description_for_image(image_bytes: bytes, user_context: str = None) -> str:
    """
    Функция для получения описания изображения (для обратной совместимости).
    
    Args:
        image_bytes: Байты изображения
        user_context: Пользовательский контекст (опционально)
        
    Returns:
        Описание изображения
    """
    agent = get_agent()
    return await agent.get_description_for_image(image_bytes, user_context)


def get_description_for_image_test(image_bytes: bytes, user_context: str = None) -> str:
    """
    Тестовая функция для получения описания изображения (для обратной совместимости).
    
    Args:
        image_bytes: Байты изображения
        user_context: Пользовательский контекст (опционально)
        
    Returns:
        Тестовое описание
    """
    agent = get_agent()
    return agent._get_description_for_image_test(image_bytes, user_context)


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    async def main():
        agent = Agent()
        
        # Пример: загрузка изображения из файла
        with open("test_image.jpg", "rb") as f:
            image_bytes = f.read()

        description = await agent.get_description_for_image(
            image_bytes=image_bytes,
            user_context="Это археологический артефакт"
        )
        print(f"Описание: {description}")
        
        # Получение статистики
        db_stats = await agent.db.get_stats()
        vector_stats = agent.vector_db.get_stats()
        print(f"Статистика БД: {db_stats}")
        print(f"Статистика векторной БД: {vector_stats}")
    
    asyncio.run(main())
