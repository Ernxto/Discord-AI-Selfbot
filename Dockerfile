# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for logs
RUN mkdir -p /app/logs

# Run the bot
CMD ["python3", "final_smart.py"]
