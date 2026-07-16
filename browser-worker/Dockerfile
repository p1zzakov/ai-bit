FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY login_debug.py ./login_debug.py
COPY presets.json ./presets.json
COPY crawler.py ./crawler.py
COPY build_patch.py ./build_patch.py
COPY crawler_patch.py ./crawler_patch.py
RUN python ./build_patch.py \
    && python ./crawler_patch.py \
    && python -m py_compile ./app.py ./login_debug.py ./crawler.py
RUN mkdir -p /app/artifacts /app/state

EXPOSE 8090
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
