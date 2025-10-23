import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from base64 import b64encode
import mimetypes  # Import модуль mimetypes

# Загружаем переменные окружения из файла .env
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")  # Получаем API ключ из переменных окружения


def encode_image(image_path):
    """Кодирует изображение в base64."""
    with open(image_path, "rb") as image_file:
        return b64encode(image_file.read()).decode('utf-8')


def process_image_with_llm(image_path, system_prompt, user_prompt, context=None, model_name="gpt-4o"):
    """Обрабатывает изображение с помощью языковой модели."""

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения. Пожалуйста, установите его.")

    chat = ChatOpenAI(model_name=model_name, openai_api_key=openai_api_key, max_tokens=1024)

    base64_image = encode_image(image_path)

    # Определяем MIME тип изображения
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
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
    result = chat.invoke(messages)  # Pass the list of messages directly to invoke
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
        # You can now pass the model name as a parameter
        response = process_image_with_llm(image_file, system_prompt, user_prompt, context,
                                          model_name="gpt-4o")
        print("Ответ LLM:", response)
    except Exception as e:
        print(f"Произошла ошибка: {e}")