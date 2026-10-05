import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-educational-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
_allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [
    host.strip()
    for host in _allowed_hosts.replace(",", " ").split()
    if host.strip()
]
if "test" in sys.argv and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "anatomy",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "espweb.middleware.RequestLogMiddleware",
]

ROOT_URLCONF = "espweb.urls"
WSGI_APPLICATION = "espweb.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "anatomy.context_processors.project",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

LANGUAGE_CODE = "es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ESP_CORE_BASE_URL = os.environ.get("ESP_CORE_BASE_URL", "http://esp-core:8080")
ESP_CORE_TIMEOUT = float(os.environ.get("ESP_CORE_TIMEOUT", "3"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "esp": {"format": "ESP-WEB | %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "esp",
        },
    },
    "loggers": {
        "esp.web": {
            "handlers": ["console"],
            "level": os.environ.get("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
