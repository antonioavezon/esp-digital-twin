FROM docker.io/library/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=espweb.settings \
    DJANGO_SECRET_KEY=build-collectstatic-only \
    DJANGO_DEBUG=0 \
    ESP_WEB_PORT=8000

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin esp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py .
COPY espweb ./espweb
COPY anatomy ./anatomy
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod 755 /usr/local/bin/docker-entrypoint.sh \
    && python manage.py collectstatic --noinput \
    && chown -R esp:esp /app

USER esp
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=25s --retries=5 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health/' % os.environ.get('ESP_WEB_PORT', '8000'))"

ENTRYPOINT ["docker-entrypoint.sh"]
