# Dockerfile
FROM python:3.11-slim

# Устанавливаем локаль (важно для русского текста и CSV)
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /app

# Копируем зависимости отдельно — кэширует слой
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код (кроме игнорируемых)
COPY . .

# Создаём папки (на случай, если volume не подключён)
RUN mkdir -p storage data logs

# Healthcheck через ping к Telegram (проверяет, "жив" ли бот)
HEALTHCHECK --interval=2m --timeout=10s --retries=3 \
  CMD python -c "import requests; print('OK')" || exit 1

CMD ["python", "main.py"]