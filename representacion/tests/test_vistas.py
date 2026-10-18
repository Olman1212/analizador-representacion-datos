"""Pruebas de las vistas con el cliente de pruebas de Django (petición HTTP simulada)."""

from django.test import TestCase
from django.urls import reverse


class VistaNumerosTests(TestCase):
    url = reverse("representacion:numeros")

    def test_pagina_inicial_sin_errores(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "representacion/numeros.html")
        self.assertTemplateUsed(respuesta, "representacion/base.html")
        self.assertContains(respuesta, "Conversión entre bases")
        self.assertNotContains(respuesta, 'role="alert"')
        self.assertIsNone(respuesta.context["resultado"])

    def test_conversion_valida(self):
        respuesta = self.client.get(self.url, {"numero": "FF", "base": "16"})
        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.context["resultado"]
        self.assertEqual((resultado.decimal, resultado.binario, resultado.octal, resultado.hexadecimal),
                         ("255", "11111111", "377", "FF"))
        self.assertContains(respuesta, "<code>11111111</code>", html=True)
        self.assertContains(respuesta, "<code>377</code>", html=True)

    def test_256_se_muestra_con_16_bits(self):
        respuesta = self.client.get(self.url, {"numero": "256", "base": "10"})
        self.assertContains(respuesta, "<code>00000001 00000000</code>", html=True)
        self.assertContains(respuesta, "bits significativos")
        self.assertEqual(respuesta.context["resultado"].bytes_necesarios, 2)

    def test_error_de_digito_invalido(self):
        respuesta = self.client.get(self.url, {"numero": "12", "base": "2"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(respuesta.context["resultado"])
        self.assertContains(respuesta, "no es un dígito válido en base 2")

    def test_error_de_rango(self):
        respuesta = self.client.get(self.url, {"numero": "70000", "base": "10"})
        self.assertContains(respuesta, "fuera de rango")
        self.assertIsNone(respuesta.context["resultado"])

    def test_error_valor_negativo(self):
        respuesta = self.client.get(self.url, {"numero": "-5", "base": "10"})
        self.assertContains(respuesta, "No se admiten valores negativos")

    def test_error_entrada_vacia(self):
        respuesta = self.client.get(self.url, {"numero": "", "base": "10"})
        self.assertContains(respuesta, "La entrada está vacía")


class VistaTextoTests(TestCase):
    url = reverse("representacion:texto")

    def test_pagina_inicial(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "representacion/texto.html")

    def test_texto_con_enie(self):
        respuesta = self.client.get(self.url, {"texto": "Año"})
        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.context["resultado"]
        self.assertEqual((resultado.total_caracteres, resultado.total_bytes), (3, 4))
        self.assertContains(respuesta, "U+00F1")
        self.assertContains(respuesta, "0xF1")
        self.assertContains(respuesta, "<code>C3 B1</code>", html=True)
        self.assertContains(respuesta, "<code>41 C3 B1 6F</code>", html=True)

    def test_texto_vacio(self):
        respuesta = self.client.get(self.url, {"texto": ""})
        self.assertContains(respuesta, "El texto está vacío")

    def test_texto_demasiado_largo(self):
        respuesta = self.client.get(self.url, {"texto": "a" * 21})
        self.assertContains(respuesta, "El texto tiene 21 caracteres y el máximo es 20")
        self.assertIsNone(respuesta.context["resultado"])

    def test_favicon_redirige_al_icono_estatico(self):
        respuesta = self.client.get("/favicon.ico")
        self.assertRedirects(respuesta, "/static/representacion/favicon.svg", status_code=301,
                             fetch_redirect_response=False)

    def test_el_texto_se_escapa_en_html(self):
        respuesta = self.client.get(self.url, {"texto": "<script>"})
        self.assertNotContains(respuesta, "<script>")
        self.assertContains(respuesta, "&lt;script&gt;")
