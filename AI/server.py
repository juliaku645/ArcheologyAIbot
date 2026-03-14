from flask import Flask, request, jsonify
import asyncio
import base64
import sys
import os

# Добавляем путь к agent.py (если файлы в одной папке)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import get_description_for_image  # Импортируем готовую функцию!

app = Flask(__name__)

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
