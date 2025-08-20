FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary code
COPY bot/ ./bot/

# Create non-root user first
RUN useradd -m -u 1000 bot

# Create directories for persistent data and set ownership
RUN mkdir -p /app/logs && chown -R bot:bot /app

USER bot

# Run the bot
CMD ["python", "bot/main.py"] 