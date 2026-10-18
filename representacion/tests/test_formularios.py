"""Pruebas de los formularios: qué errores aparecen y en qué campo."""

from django.test import TestCase

from representacion.forms import ConversionForm, TextoForm


class ConversionFormTests(TestCase):
    def test_datos_validos_dejan_el_resultado(self):
        formulario = ConversionForm({"numero": "FF", "base": "16"})
        self.assertTrue(formulario.is_valid())
        self.assertEqual(formulario.cleaned_data["base"], 16)
        self.assertEqual(formulario.cleaned_data["resultado"].valor, 255)

    def test_cada_error_tiene_su_codigo(self):
        casos = [
            ({"numero": "", "base": "10"}, "vacio"),
            ({"numero": "-5", "base": "10"}, "negativo"),
            ({"numero": "12", "base": "2"}, "digito_invalido"),
            ({"numero": "70000", "base": "10"}, "fuera_de_rango"),
        ]
        for datos, codigo in casos:
            with self.subTest(datos=datos):
                formulario = ConversionForm(datos)
                self.assertFalse(formulario.is_valid())
                self.assertTrue(formulario.has_error("numero", code=codigo))

    def test_base_no_permitida(self):
        formulario = ConversionForm({"numero": "10", "base": "7"})
        self.assertFalse(formulario.is_valid())
        self.assertTrue(formulario.has_error("base", code="invalid_choice"))
        self.assertIn("La base «7» no es válida", formulario.errors["base"][0])


class TextoFormTests(TestCase):
    def test_texto_valido_conserva_los_espacios(self):
        formulario = TextoForm({"texto": " Año "})
        self.assertTrue(formulario.is_valid())
        self.assertEqual(formulario.cleaned_data["resultado"].total_caracteres, 5)

    def test_texto_vacio_y_demasiado_largo(self):
        self.assertTrue(TextoForm({"texto": ""}).has_error("texto", code="texto_vacio"))
        self.assertTrue(TextoForm({"texto": "x" * 21}).has_error("texto", code="texto_largo"))
