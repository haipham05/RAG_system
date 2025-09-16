FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 \
       libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy and install Python dependencies first (for better caching)
COPY src/requirements.txt /app/requirements.txt

# Install dependencies with optimization flags
RUN pip install --no-cache-dir --compile -r /app/requirements.txt \
    && pip cache purge \
    && find /usr/local -type d -name __pycache__ -exec rm -rf {} + || true

# Copy application source
COPY src/ /app/src/

EXPOSE 8080

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting RAG system initialization..."\n\
python src/initialize.py\n\
echo "Initialization complete. Starting API server..."\n\
uvicorn src.main:app --host 0.0.0.0 --port 8080\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]


