# --- CryptoForget recommendation model — serving image ---
FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; scikit-learn/scipy wheels are precompiled.
COPY serving/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Project source (the model/personalization logic Vedant wrote)
COPY src/ ./src/

# API layer
COPY serving/app/ ./app/

# Pre-built model artifacts (run serving/scripts/build_content_model.py
# locally or in CI *before* building this image — see serving/README.md).
COPY serving/models/ ./models/

ENV MODELS_DIR=/app/models \
    MODEL_VERSION=dev \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
