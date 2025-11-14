import base64
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
# from base64 import b64encode
# import mimetypes
import asyncio
from app.database import get_image_blob_from_db,  select_user_id

# Загружаем переменные окружения из файла .env
load_dotenv()
load_dotenv(encoding='utf-8-sig')

openai_api_key = os.getenv("OPENAI_API_KEY")


def image_bytes_to_base64(image_bytes):
    """Кодирует байтовый объект изображения в base64."""
    return base64.b64encode(image_bytes).decode('utf-8')
async def process_image_to_llm(image_bytes, system_prompt, user_prompt, context=None, model_name="gpt-4o"):

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения. Пожалуйста, установите его.")

    chat = ChatOpenAI(model_name = model_name, openai_api_key = openai_api_key, max_tokens=1024)


    # Перевод в base64
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
                messages.append(HumanMessage(content=item["content"]))  # Convert user messages to HumanMessage objects
            elif item["role"] == "assistant":
                messages.append(
                    SystemMessage(content=item["content"]))  # Convert assistant messages to SystemMessage objects

    messages.append(HumanMessage(content=content))  # Convert content to HumanMessage object

    # Вызываем модель
    result = await chat.ainvoke(messages)  # Pass the list of messages directly to invoke
    return result.content  # Возвращаем ответ модели



async def get_description_for_image(base64_image):

    system_prompt = os.getenv('SYSTEM_PROMPT')
    # system_prompt = ''
    user_prompt = "Опиши, что ты видишь на этом изображении."
    context = [
        {"role": "user", "content": "Я хочу узнать больше об этом месте."},
        {"role": "assistant", "content": "Хорошо, что вы хотите знать?"}
    ]

    try:
        # You can now pass the model name as a parameter
        response = await process_image_to_llm(base64_image, system_prompt, user_prompt, context, model_name="gpt-4o")
        print("Ответ LLM:", response)
        return response
    except Exception as e:
        print(f"Произошла ошибка: {e}")


async def main():
    user_id = select_user_id()
    image_bytes = await get_image_blob_from_db(user_id)  # await важен
    if image_bytes is None:
        print("Изображение не найдено в базе данных")
        return
    description = await get_description_for_image(image_bytes)
    print(description)

if __name__ == "__main__":
    asyncio.run(main())










