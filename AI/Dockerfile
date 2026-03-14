FROM python:3.11-slim

WORKDIR /app

# SQLite встроен в Python, дополнительные зависимости не требуются
# Копирование requirements
COPY /requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения Только .py файлы
COPY *.py /app/

# Открытие порта
EXPOSE 5000

# Запуск приложения
CMD ["python", "server.py"]
