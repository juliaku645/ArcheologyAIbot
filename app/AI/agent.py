import base64
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class Agent:
    def __init__(self):
        load_dotenv(encoding='utf-8-sig')
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = "gpt-4o"
        self.is_test = os.getenv("IS_TEST") or False

    async def __process_image_to_llm(self, image_bytes, system_prompt, user_prompt, context=None):

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения. Пожалуйста, установите его.")

        chat = ChatOpenAI(model_name=self.model_name, openai_api_key=self.openai_api_key, max_tokens=1024)

        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Определяем MIME тип изображения

        mime_type = "image/jpeg"  # По умолчанию JPEG, если MIME тип не удалось определить

        # Validate MIME type: Ensure it's an actual image type
        if not mime_type.startswith("image/"):
            raise ValueError(f"Invalid MIME type: {mime_type}. Only image types are supported.")

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

        messages = [
            SystemMessage(content=system_prompt),  # Convert system_prompt to SystemMessage object
        ]
        if context:
            for item in context:
                if item["role"] == "user":
                    messages.append(
                        HumanMessage(content=item["content"]))  # Convert user messages to HumanMessage objects
                elif item["role"] == "assistant":
                    messages.append(
                        SystemMessage(content=item["content"]))  # Convert assistant messages to SystemMessage objects

        messages.append(HumanMessage(content=content))  # Convert content to HumanMessage object

        # Вызываем модель
        result = await chat.ainvoke(messages)  # Pass the list of messages directly to invoke
        return result.content  # Возвращаем ответ модели

    def __get_description_for_image_test(self, base64_image, user_context=None):
        print(f"Картинка:{base64_image is not None}, user_context: {user_context} ")
        return "Очень красивая картинка"

    async def __get_description_for_image(self, base64_image, user_context=None):

        system_prompt = os.getenv('SYSTEM_PROMPT')
        user_prompt = user_context
        context = [
            {"role": "user", "content": "Я хочу узнать больше об этом месте."},
            {"role": "assistant", "content": "Хорошо, что вы хотите знать?"}
        ]

        try:
            # You can now pass the model name as a parameter
            response = await self.__process_image_to_llm(
                base64_image,
                system_prompt,
                user_prompt,
                context
            )
            print("Ответ LLM:", response)
            return response
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    async def get_description_for_image(self, base64_image, user_context=None):
        if self.is_test:
            return self.__get_description_for_image_test(base64_image, user_context)
        else:
            return await self.__get_description_for_image(base64_image, user_context)
