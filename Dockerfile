FROM python:3.10

WORKDIR /app

# Копируем файл requirements.txt
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

CMD ["python", "my_teleram_bot.py"]

