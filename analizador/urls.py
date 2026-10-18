"""Rutas del proyecto: todas las páginas las atiende la app «representacion»."""

from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", include("representacion.urls")),
    # Los navegadores piden /favicon.ico aunque la página indique otro icono.
    path("favicon.ico", RedirectView.as_view(url=static("representacion/favicon.svg"), permanent=True)),
]
