"""Datos del entorno de ejecución para el pie de página (útiles como evidencia)."""

import platform
import socket
from pathlib import Path

import django

_ENTORNO = {
    "python": platform.python_version(),
    "django": django.get_version(),
    # Dentro de Docker el nombre del equipo es el ID corto del contenedor.
    "equipo": socket.gethostname(),
    "en_contenedor": Path("/.dockerenv").exists(),
}


def entorno(request):
    return {
        "entorno": {
            **_ENTORNO,
            # gunicorn/26.x con gunicorn; WSGIServer/0.2 con runserver.
            "servidor": request.META.get("SERVER_SOFTWARE", "desconocido"),
        }
    }
