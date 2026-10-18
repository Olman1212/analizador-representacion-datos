"""Pruebas de la lógica de conversión (converters.py), sin pasar por las vistas."""

from django.test import TestCase

from representacion.converters import (
    ErrorValidacion,
    analizar_texto,
    a_decimal,
    binario_relleno,
    convertir,
    desde_decimal,
)


class ConversionesValidasTests(TestCase):
    def test_hexadecimal_ff_en_las_cuatro_bases(self):
        r = convertir("FF", 16)
        self.assertEqual(r.valor, 255)
        self.assertEqual(r.decimal, "255")
        self.assertEqual(r.binario, "11111111")
        self.assertEqual(r.octal, "377")
        self.assertEqual(r.hexadecimal, "FF")

    def test_255_ocupa_8_bits_y_256_ocupa_16(self):
        r255 = convertir("255", 10)
        self.assertEqual(r255.binario, "11111111")
        self.assertEqual((r255.bits_significativos, r255.bytes_necesarios), (8, 1))

        r256 = convertir("256", 10)
        self.assertEqual(r256.binario, "0000000100000000")
        self.assertEqual(len(r256.binario), 16)
        self.assertEqual((r256.bits_significativos, r256.bytes_necesarios), (9, 2))
        self.assertEqual(r256.bits_relleno, 7)

    def test_relleno_hasta_multiplo_de_byte(self):
        self.assertEqual(binario_relleno(5), "00000101")
        self.assertEqual(binario_relleno(127), "01111111")
        self.assertEqual(binario_relleno(4095), "0000111111111111")

    def test_cero_se_muestra_con_8_bits(self):
        r = convertir("0", 10)
        self.assertEqual(r.binario, "00000000")
        self.assertEqual((r.bits_significativos, r.bytes_necesarios), (1, 1))

    def test_maximo_65535(self):
        r = convertir("65535", 10)
        self.assertEqual(r.binario, "1" * 16)
        self.assertEqual(r.octal, "177777")
        self.assertEqual(r.hexadecimal, "FFFF")
        self.assertEqual(r.bytes_necesarios, 2)

    def test_entradas_en_binario_y_octal(self):
        self.assertEqual(convertir("1010", 2).valor, 10)
        self.assertEqual(convertir("777", 8).valor, 511)

    def test_minusculas_prefijos_y_separadores(self):
        self.assertEqual(convertir("ff", 16).valor, 255)
        self.assertEqual(convertir("0xFF", 16).valor, 255)
        self.assertEqual(convertir("0b1010", 2).valor, 10)
        self.assertEqual(convertir("0o17", 8).valor, 15)
        self.assertEqual(convertir("  1111 0000 ", 2).valor, 240)
        self.assertEqual(convertir("FF_FF", 16).valor, 65535)

    def test_coincide_con_las_funciones_de_python(self):
        """El algoritmo propio debe dar lo mismo que int() y format()."""
        for valor in [0, 1, 7, 8, 9, 15, 16, 127, 128, 255, 256, 1000, 4095, 4096, 65535]:
            for base, formato in [(2, "b"), (8, "o"), (10, "d"), (16, "X")]:
                with self.subTest(valor=valor, base=base):
                    texto = format(valor, formato)
                    self.assertEqual(desde_decimal(valor, base), texto)
                    self.assertEqual(a_decimal(texto, base), int(texto, base))

    def test_desarrollo_posicional(self):
        terminos = convertir("FF", 16).desarrollo_posicional
        self.assertEqual([(t["valor_digito"], t["exponente"], t["valor"]) for t in terminos], [(15, 1, 240), (15, 0, 15)])


class ErroresDeConversionTests(TestCase):
    def assertError(self, codigo, entrada, base=10):
        with self.assertRaises(ErrorValidacion) as contexto:
            convertir(entrada, base)
        self.assertEqual(contexto.exception.codigo, codigo)
        return contexto.exception.mensaje

    def test_digito_invalido_para_la_base(self):
        mensaje = self.assertError("digito_invalido", "102", base=2)
        self.assertIn("«2» no es un dígito válido en base 2", mensaje)
        self.assertError("digito_invalido", "8", base=8)
        self.assertError("digito_invalido", "1A", base=10)
        self.assertError("digito_invalido", "FG", base=16)

    def test_digitos_unicode_no_se_aceptan(self):
        # int("١٢") devolvería 12: por eso se validan los dígitos a mano.
        self.assertError("digito_invalido", "١٢", base=10)
        self.assertError("digito_invalido", "１２", base=10)

    def test_valor_fuera_de_rango(self):
        mensaje = self.assertError("fuera_de_rango", "65536")
        self.assertIn("fuera de rango", mensaje)
        self.assertError("fuera_de_rango", "10000", base=16)
        self.assertError("fuera_de_rango", "1" * 17, base=2)

    def test_valor_negativo(self):
        mensaje = self.assertError("negativo", "-5")
        self.assertIn("negativos", mensaje)

    def test_entrada_vacia(self):
        self.assertError("vacio", "")
        self.assertError("vacio", "   ")
        self.assertError("vacio", "0x", base=16)

    def test_base_no_permitida(self):
        self.assertError("base_invalida", "10", base=7)


class AnalisisTextoTests(TestCase):
    def test_ano_tiene_3_caracteres_y_4_bytes(self):
        analisis = analizar_texto("Año")
        self.assertEqual(analisis.total_caracteres, 3)
        self.assertEqual(analisis.total_bytes, 4)
        self.assertEqual(analisis.utf8_hex, "41 C3 B1 6F")

        enie = analisis.caracteres[1]
        self.assertEqual(enie.caracter, "ñ")
        self.assertEqual(enie.codigo, 241)
        self.assertEqual(enie.punto_codigo, "U+00F1")
        self.assertEqual(enie.hexadecimal, "0xF1")
        self.assertEqual(enie.utf8_hex, "C3 B1")
        self.assertEqual(enie.utf8_binario, "11000011 10110001")
        self.assertEqual(enie.num_bytes, 2)

    def test_caracteres_de_1_a_4_bytes(self):
        casos = {"A": ("U+0041", "41"), "€": ("U+20AC", "E2 82 AC"), "😀": ("U+1F600", "F0 9F 98 80")}
        for caracter, (punto, utf8) in casos.items():
            with self.subTest(caracter=caracter):
                info = analizar_texto(caracter).caracteres[0]
                self.assertEqual(info.punto_codigo, punto)
                self.assertEqual(info.utf8_hex, utf8)

    def test_los_espacios_cuentan_como_caracteres(self):
        analisis = analizar_texto("a b")
        self.assertEqual(analisis.total_caracteres, 3)
        self.assertEqual(analisis.caracteres[1].visible, "(espacio)")

    def test_texto_vacio(self):
        for texto in ["", "   "]:
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion) as contexto:
                    analizar_texto(texto)
                self.assertEqual(contexto.exception.codigo, "texto_vacio")

    def test_texto_de_mas_de_20_caracteres(self):
        self.assertEqual(analizar_texto("a" * 20).total_caracteres, 20)
        with self.assertRaises(ErrorValidacion) as contexto:
            analizar_texto("a" * 21)
        self.assertEqual(contexto.exception.codigo, "texto_largo")
        self.assertIn("21 caracteres", contexto.exception.mensaje)
