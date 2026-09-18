# --- CryptoForget recommendation model — serving image ---
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and application package
COPY src/ ./src/
COPY app/ ./app/
COPY main.py ./main.py
COPY scripts/ ./scripts/

# Copy pre-built model artifacts
COPY models/ ./models/

ENV MODELS_DIR=/app/models \
    MODEL_VERSION=dev \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
