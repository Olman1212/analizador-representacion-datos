"""
Configuración de Django para el «Analizador de representación de datos».

Los valores que cambian entre el entorno local (runserver) y el contenedor
(gunicorn) se leen de variables de entorno, con valores por defecto pensados
para desarrollo:

    DJANGO_SECRET_KEY     clave secreta (obligatorio cambiarla en producción)
    DJANGO_DEBUG          "1" activa el modo depuración, "0" lo desactiva
    DJANGO_ALLOWED_HOSTS  lista separada por comas de nombres de host válidos
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(nombre, por_defecto):
    return os.environ.get(nombre, por_defecto).strip().lower() in {"1", "true", "si", "sí", "yes"}


def _env_lista(nombre, por_defecto):
    return [valor.strip() for valor in os.environ.get(nombre, por_defecto).split(",") if valor.strip()]


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-solo-para-desarrollo-cambiar-en-produccion",
)

DEBUG = _env_bool("DJANGO_DEBUG", "1")

ALLOWED_HOSTS = _env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")


# Aplicaciones: solo lo imprescindible. La app no usa usuarios, sesiones ni
# administración, así que no hace falta ejecutar migraciones.

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "representacion",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    # Con gunicorn (DEBUG=0) los archivos estáticos los sirve WhiteNoise desde
    # STATIC_ROOT; en desarrollo ya los sirve runserver.
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "analizador.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "representacion.context_processors.entorno",
            ],
        },
    },
]

WSGI_APPLICATION = "analizador.wsgi.application"


# Base de datos: la configuración SQLite de serie. La app no define modelos
# ni guarda nada; runserver crea un db.sqlite3 vacío al comprobar las
# migraciones, gunicorn ni siquiera lo abre y las pruebas usan una base de
# datos temporal en memoria.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Internacionalización: interfaz y mensajes de Django en español.

LANGUAGE_CODE = "es"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Archivos estáticos (CSS). «collectstatic» los copia a STATIC_ROOT y
# WhiteNoise los sirve comprimidos.

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Registro en la salida estándar para verlo con «docker logs» o «docker compose logs».

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"consola": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["consola"], "level": "INFO"},
    # Sustituye la configuración de serie de Django para no duplicar líneas.
    "loggers": {"django": {"handlers": ["consola"], "level": "INFO", "propagate": False}},
}
