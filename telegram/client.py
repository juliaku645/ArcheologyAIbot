
from flask import Flask, request, jsonify
import asyncio
import base64
from typing import Optional

app = Flask(__name__)


# Заглушки для совместимости (замените на реальные импорты)
async def get_agent():
    """Получает агента для анализа изображений."""
    # Здесь импорт или инициализация вашего агента
    pass  # Например: from your_module import Agent; return Agent()


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


@app.route('/describe', methods=['POST'])
async def describe_image():
    """
    Эндпоинт для получения описания изображения.

    JSON body:
    {
        "image_b64": "base64-encoded image bytes",
        "user_context": "optional context"
    }

    Returns:
    {
        "description": "str"
    }
    """
    try:
        data = request.get_json()
        image_b64 = data.get('image_b64')
        user_context = data.get('user_context', None)

        if not image_b64:
            return jsonify({'error': 'image_b64 required'}), 400

        image_bytes = base64.b64decode(image_b64)

        # Вызов асинхронной функции
        description = await get_description_for_image(image_bytes, user_context)

        return jsonify({'description': description})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Запуск с Quart для полной async поддержки (pip install quart[async])
    # Или используйте uvicorn: uvicorn server:app --reload
    import asyncio
    from quart import Quart  # Альтернатива: используйте Quart для чистого async Flask

    # Для чистого Flask 2.0+ с ASGI (uvicorn server:app --app-dir .)
    app.run(debug=True)
