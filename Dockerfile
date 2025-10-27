# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema mínimo
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV CHECK_INTERVAL_MINUTES=60

CMD ["python", "bot.py"]
