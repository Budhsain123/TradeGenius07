# Base image
FROM python:3.11-slim

# Environment clean & fast
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# System deps (optional but safe)
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy zip
COPY FilesStoreBot.zip /app/

# Extract project
RUN unzip FilesStoreBot.zip && rm FilesStoreBot.zip

# Install requirements if exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Auto start (NO COMMAND NEEDED FROM USER)
CMD ["python", "main.py"]
