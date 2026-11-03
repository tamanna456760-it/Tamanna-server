FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10001 --create-home tamanna \
    && mkdir -p /app/data \
    && chown -R tamanna:tamanna /app

COPY --chown=tamanna:tamanna . .

USER tamanna
EXPOSE 8000

CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "60", "--bind", "0.0.0.0:8000", "app:app"]
