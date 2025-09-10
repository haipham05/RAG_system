FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create data directory
RUN mkdir -p /app/data/pdfs

# Expose port for FastAPI
EXPOSE 8000

# Startup script that processes PDFs and starts API
CMD ["python", "startup.py"]
