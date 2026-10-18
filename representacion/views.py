"""
Vistas de la app.

Los formularios se envían por GET: la operación no modifica nada en el
servidor y así cada resultado tiene una URL que se puede repetir o compartir,
por ejemplo /?numero=FF&base=16 o /texto/?texto=Año.
"""

from django.shortcuts import render

from .forms import ConversionForm, TextoForm

EJEMPLOS_NUMEROS = [
    {"numero": "FF", "base": 16, "valido": True},
    {"numero": "255", "base": 10, "valido": True},
    {"numero": "256", "base": 10, "valido": True},
    {"numero": "0", "base": 10, "valido": True},
    {"numero": "1010", "base": 2, "valido": True},
    {"numero": "177777", "base": 8, "valido": True},
    {"numero": "12", "base": 2, "valido": False},
    {"numero": "-5", "base": 10, "valido": False},
    {"numero": "70000", "base": 10, "valido": False},
]

EJEMPLOS_TEXTO = ["Año", "Hola", "ñandú", "€ 5", "😀", "日本"]


def conversion_numerica(request):
    formulario = ConversionForm(request.GET or None)
    resultado = formulario.cleaned_data["resultado"] if formulario.is_valid() else None
    return render(request, "representacion/numeros.html", {
        "formulario": formulario,
        "resultado": resultado,
        "ejemplos": EJEMPLOS_NUMEROS,
    })


def analisis_texto(request):
    formulario = TextoForm(request.GET or None)
    resultado = formulario.cleaned_data["resultado"] if formulario.is_valid() else None
    return render(request, "representacion/texto.html", {
        "formulario": formulario,
        "resultado": resultado,
        "ejemplos": EJEMPLOS_TEXTO,
    })
