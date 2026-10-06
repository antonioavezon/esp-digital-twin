FROM docker.io/library/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ESP_CORE_HOST=0.0.0.0 \
    ESP_CORE_PORT=8080 \
    ESP_DATA_ROOT=/app/data \
    LOG_LEVEL=INFO

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin esp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY pytest.ini .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod 755 /usr/local/bin/docker-entrypoint.sh \
    && chown -R esp:esp /app

USER esp
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('ESP_CORE_PORT', '8080'))"

ENTRYPOINT ["docker-entrypoint.sh"]
