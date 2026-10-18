# Imagen del «Analizador de representación de datos»: Django servido con gunicorn.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    DJANGO_DEBUG=0 \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
    WEB_CONCURRENCY=2

WORKDIR /app

# Primero solo las dependencias: esta capa se reutiliza mientras
# requirements.txt no cambie, aunque cambie el código.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Copia el CSS a /app/staticfiles para que WhiteNoise lo sirva y crea un
# usuario sin privilegios. El código queda como propiedad de root: el
# proceso de la app puede leerlo, pero no modificarlo.
RUN python manage.py collectstatic --noinput \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=2)"]

# WEB_CONCURRENCY fija el número de procesos de gunicorn (2 caben de sobra en 256 MB).
# El socket de control de gunicorn no hace falta y necesitaría un directorio personal.
CMD ["gunicorn", "analizador.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--worker-tmp-dir", "/dev/shm", \
     "--no-control-socket", \
     "--access-logfile", "-"]
