import os
import base64
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI  # <-- Исправленный импорт
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_core.runnables import chain
from langchain_core.output_parsers import StrOutputParser
#from langchain.llms import OpenAI
from langchain_community.llms import OpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import BaseOutputParser

# 1. Загрузка API ключа
load_dotenv()
openai_api_key = os.getenv

# 2. Инициализация языковой модели OpenAI
llm = OpenAI(openai_api_key=openai_api_key)

#def sendMessage(message: str, image: ??):

print('b')


print(1)
def encode_image(self, image_path: str) -> str:
        #Кодирование изображения в base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

print(1)
def process_image_with_prompt(
            self,
            image_path: str,
            system_prompt: str = "Ты всемирно извсетный доктор исторических наук со стажем 50+ лет, который анализирует изображения и отвечает на вопросы о них.",
            user_message: Optional[str] = None,
            image_detail: str = "auto"
    ) -> str:

        base64_image = self.encode_image(image_path)
        print(1)
        # Формируем контент сообщения
        message_content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": image_detail
                }
            }
        ]

        print(1)

        # Добавляем текстовое сообщение, если оно есть
        if user_message:
            message_content.insert(0, {
                "type": "text",
                "text": user_message
            })

        # Создаем сообщения для нейросети
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message_content)
        ]

        # Отправляем запрос
        response = self.llm.invoke(messages)
        return response.content

def process_text_only(self, message: str, system_prompt: str = "Ты историк") -> str:
        """Обработка только текстового сообщения"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]

        response = self.llm.invoke(messages)
        return response.content;
print(1)
print(f"Ответ: {response}")


# Функция для кодирования изображения в base64
def encode_image(image_path):
    """Encodes an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def process_image_with_llm(image_path, system_prompt, user_prompt=None, context=None):

    base64_image = encode_image(image_path)  # Encode the image

    # Construct the messages to send to the model
    messages = []
    messages.append(SystemMessage(content=system_prompt))  # Add system prompt

    if context:  # Add context messages
        for msg in context:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(SystemMessage(content=msg["content"])) # or AIMessage, depending on what your model understands

    # Build the content of the user message including the image
    content = []
    if user_prompt:
        content.append({"type": "text", "text": user_prompt})  # Add the text prompt

    content.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"  # Adjust image type if needed
        }
    })

    messages.append(HumanMessage(content=content))  # Add the user's message including image and prompt

    # Initialize the ChatOpenAI model with gpt-4-vision-preview
    chat = ChatOpenAI(model_name="gpt-4-vision-preview", api_key=openai_api_key, max_tokens=1024)  # You need an OpenAI key with access to gpt-4-vision-preview

    # Invoke the model
    result = chat.invoke(messages)
    return result.content  # Return the model's response


# Example Usage:
#if __name__ == "__main__":
    image_file = "path/to/your/image.jpg"  # Replace with the path to your image
    system_prompt = "You are a helpful assistant that analyzes images and answers questions. Be concise."
    user_prompt = "Describe what you see in this image."
    context = [
        {"role": "user", "content": "I want to know more about this place."},
        {"role": "assistant", "content": "Okay, what do you want to know?"}
    ]

    #try:
    response = process_image_with_llm(image_file, system_prompt, user_prompt, context)
    print("LLM Response:", response)
#except Exception as e:
   # print(f"An error occurred: {e}")
