
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import aiohttp
import json
import base64
from typing import Optional
import asyncio

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


#async def get_description_for_image_test(base64_image, user_context=None):
    print(f"Картинка:{base64_image is not None}, user_context: {user_context} ")
    return "Очень красивая картинка"
async def get_description_for_image(image_bytes: bytes, user_context: Optional[str] = None) -> str:
    """
       Вызывает POST /describe на server.py через HTTP.
       """
    SERVER_URL = "http://localhost:5000"

    # Кодируем image_bytes обратно в base64
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    payload = {
        "imageB64": image_b64,
        "userContext": user_context or ""
    }

    print(f"SENDING to {SERVER_URL}/describe: {len(image_bytes)} bytes")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{SERVER_URL}/describe",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=120)
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    description = result.get('description', 'No description')
                    print(f"RECEIVED: {description[:100]}...")
                    return description
                else:
                    error_text = await response.text()
                    print(f"SERVER ERROR {response.status}: {error_text}")
                    raise ValueError(f"Server returned {response.status}: {error_text}")

    except aiohttp.ClientError as e:
        print(f"HTTP ERROR: {str(e)}")
        raise ValueError(f"Cannot reach server: {str(e)}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise ValueError(f"Processing failed: {str(e)}")


# async def get_description_for_image(image_bytes: bytes, user_context: Optional[str] = None) -> str:
#     """
#     Получает описание изображения используя OpenAI GPT-4o.
#
#     Args:
#         image_bytes: Байты изображения (не base64!)
#         user_context: Пользовательский контекст
#
#     Returns:
#         Описание изображения
#     """
#     print(f"INFO: Agent получил изображение размером {len(image_bytes)} байт, context: {user_context}")
#
#     # Системный промпт для анализа изображения
#     system_prompt = "SYSTEM_PROMPT"
#
#     user_prompt = "Проанализируй это изображение и дай подробное описание."
#
#     try:
#         # Вызываем обработку изображения
#         description = await process_image_to_llm(
#             image_bytes=image_bytes,
#             system_prompt=system_prompt,
#             user_prompt=user_prompt,
#             context=None
#         )
#         print(f"SUCCESS: Описание сгенерировано: {description[:100]}...")
#         return description.strip()
#
#     except Exception as e:
#         print(f"ERROR в get_description_for_image: {str(e)}")
#         return f"Ошибка анализа изображения: {str(e)}"













