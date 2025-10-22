FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
  POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# instalar dependencias del sistema
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

# copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE ${PORT:-8080}

# Stage de test
FROM base AS test
RUN pip install --no-cache-dir pytest pytest-cov
CMD ["pytest", "--maxfail=1", "--disable-warnings", "-q"]

# Stage dev
FROM base AS dev
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
