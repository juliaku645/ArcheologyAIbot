from flask import Flask, request, jsonify
import asyncio
import base64
import sys
import os
from agent import Agent


app = Flask(__name__)
async def get_agent():
    print("DEBUG: Получение агента")
    return Agent()
async def get_description_for_image(image_bytes: bytes, user_context: str = None) -> str:
    """
    Функция для получения описания изображения (для обратной совместимости).

    Args:
    image_bytes: Байты изображения
    user_context: Пользовательский контекст (опционально)

Returns:
Описание изображения
"""
    print(f"INFO: Начало обработки изображения, размер: {len(image_bytes)} байт")

    agent = await get_agent()
    if agent is None:
        print("ERROR: Агент не инициализирован! Замените pass в get_agent() на реальную логику.")
        raise ValueError("Агент недоступен - реализуйте get_agent()")

    description = await agent.get_description_for_image(image_bytes, user_context)
    print(f"INFO: Описание получено: {description[:100]}...")
    return description
@app.route('/describe', methods=['POST'])
def describe_image():
    """Эндпоинт для получения описания изображения."""
    print(f"INFO: Получен POST /describe от IP: {request.remote_addr}")

    try:
        data = request.get_json()
        print(f"DEBUG: JSON данные")

        image_b64 = data.get('imageB64')
        user_context = data.get('userContext')

        if not image_b64:
            print("WARNING: Отсутствует imageB64 в запросе")
            return jsonify({'error': 'imageB64 required'}), 400

        print(f"DEBUG: Декодирование base64...")
        image_bytes = base64.b64decode(image_b64)
        print(f"INFO: Изображение: {len(image_bytes)} байт")

        # Запускаем асинхронную функцию напрямую
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        description = loop.run_until_complete(
            get_description_for_image(image_bytes, user_context)
        )
        loop.close()
        print("INFO: Обработка завершена успешно")

        return jsonify({'description': description})

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print("TRACEBACK:", traceback.format_exc())
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', 'localhost')
    try:
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("Остановка сервера...")