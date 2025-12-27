FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install python deps first (cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy rest of files
COPY . .

# auto start bot (NO manual command)
CMD ["python", "bot.py"]
