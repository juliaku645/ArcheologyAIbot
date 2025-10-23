import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from base64 import b64encode
import mimetypes  # Import модуль mimetypes

# Загружаем переменные окружения из файла .env
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")  # Получаем API ключ из переменных окружения

def encode_image(image_path):
    """Кодирует изображение в base64."""
    with open(image_path, "rb") as image_file:
        return b64encode(image_file.read()).decode('utf-8')

def process_image_with_llm(image_path, system_prompt, user_prompt, context=None):
    """Обрабатывает изображение с помощью языковой модели."""

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения. Пожалуйста, установите его.")

    chat = ChatOpenAI(model_name="-4-vision-preview", openai_api_key=openai_api_key, max_tokens=1024)
    print('A')
    base64_image = encode_image(image_path)
    print('B')
    # Определяем MIME тип изображения , _
    mime_type= mimetypes.guess_type(image_path)
    print('C')
    if not mime_type:
        mime_type = "image/jpeg"  # По умолчанию JPEG, если MIME тип не удалось определить
        print('D')
    print('E')
    content = [
        {
            "type": "text",
            "text": user_prompt
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}"  # Включаем MIME тип
            }
        }
    ]

    print('F')
    messages = [ {"role": "system", "content": system_prompt}, ]
    print(context)
    if context:
        for item in context:
            print('G')
            messages.append(item)  # Добавляем историю контекста
    print('u')
    messages.append({"role": "user", "content": content}) # Добавляем запрос с изображением
    print(messages)

    # Вызываем модель
    result = chat.invoke(messages)  # Передаем список сообщений в invoke
    print('y')
    return result.content  # Возвращаем ответ модели


# Пример использования:
if __name__ == "__main__":
    image_file = "scale_1200.jpg"  # Замените на путь к вашему изображению
    system_prompt = "Ты полезный ассистент, который анализирует изображения и отвечает на вопросы. Будь краток."
    user_prompt = "Опиши, что ты видишь на этом изображении."
    context = [
        {"role": "user", "content": "Я хочу узнать больше об этом месте."},
        {"role": "assistant", "content": "Хорошо, что вы хотите знать?"}
    ]

    try:
        response = process_image_with_llm(image_file, system_prompt, user_prompt, context)
        print("Ответ LLM:", response)
    except Exception as e:
        print(f"Произошла ошибка: {e}")