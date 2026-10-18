"""
Formularios de la app.

Los formularios solo traducen los errores de converters.py a errores de
Django; las reglas de validación viven en ese módulo para no duplicarlas.
Si los datos son válidos, el resultado queda en cleaned_data["resultado"].
"""

from django import forms

from . import converters
from .converters import ErrorValidacion


def _error_de_formulario(error: ErrorValidacion) -> forms.ValidationError:
    return forms.ValidationError(error.mensaje, code=error.codigo)


class ConversionForm(forms.Form):
    numero = forms.CharField(
        label="Número",
        # La entrada vacía la valida clean_numero para dar un mensaje propio.
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Por ejemplo: FF, 1010 o 255",
            "autocomplete": "off",
            "spellcheck": "false",
            "autocapitalize": "characters",
        }),
    )
    base = forms.TypedChoiceField(
        label="Base de origen",
        choices=[(base, f"{base} · {nombre}") for base, nombre in converters.BASES.items()],
        coerce=int,
        initial=10,
        widget=forms.RadioSelect,
        error_messages={
            "required": "Elija la base de origen: 2, 8, 10 o 16.",
            "invalid_choice": "La base «%(value)s» no es válida. Elija 2, 8, 10 o 16.",
        },
    )

    def clean_numero(self):
        """Comprobaciones que no dependen de la base: vacío, negativo y longitud."""
        try:
            return converters.limpiar_entrada(self.cleaned_data["numero"])
        except ErrorValidacion as error:
            raise _error_de_formulario(error)

    def clean(self):
        """Comprobaciones que necesitan la base: dígitos válidos y rango 0–65 535."""
        datos = super().clean()
        numero, base = datos.get("numero"), datos.get("base")
        if numero and base:
            try:
                datos["resultado"] = converters.convertir(numero, base)
            except ErrorValidacion as error:
                self.add_error("numero", _error_de_formulario(error))
        return datos


class TextoForm(forms.Form):
    texto = forms.CharField(
        label="Texto",
        required=False,
        # Los espacios también son caracteres: no se recortan.
        strip=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Por ejemplo: Año",
            "autocomplete": "off",
        }),
    )

    def clean_texto(self):
        """Texto no vacío y de 20 caracteres como máximo."""
        try:
            return converters.validar_texto(self.cleaned_data["texto"])
        except ErrorValidacion as error:
            raise _error_de_formulario(error)

    def clean(self):
        datos = super().clean()
        if "texto" in datos:
            datos["resultado"] = converters.analizar_texto(datos["texto"])
        return datos
