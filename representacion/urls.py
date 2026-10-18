from django.urls import path

from . import views

app_name = "representacion"

urlpatterns = [
    path("", views.conversion_numerica, name="numeros"),
    path("texto/", views.analisis_texto, name="texto"),
]
