FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app
RUN mkdir -p /app/reports /app/data

EXPOSE 8080
CMD ["uvicorn", "app.bootstrap:app", "--host", "0.0.0.0", "--port", "8080"]
