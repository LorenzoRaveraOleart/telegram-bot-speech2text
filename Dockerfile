# Use Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /server

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
# Copy requirements first (for better caching)
COPY server/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot files into the container
COPY server/ .

# Debugging: Check the file tree
RUN ls -l /server
RUN ls -l /

# Start the bot
CMD ["python", "/server/telegram_s3_bot.py"]
