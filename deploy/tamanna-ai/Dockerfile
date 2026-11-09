FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY vendor/tamanna-ai/requirements-server.txt ./requirements-server.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements-server.txt \
    && useradd --system --uid 10002 --create-home tamanna \
    && mkdir -p /app/data \
    && chown -R tamanna:tamanna /app

COPY --chown=tamanna:tamanna vendor/tamanna-ai/ ./

USER tamanna
EXPOSE 8000

CMD ["uvicorn", "Main:app", "--host", "0.0.0.0", "--port", "8000"]
