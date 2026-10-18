"""
Lógica de conversión numérica y de análisis de caracteres.

Este módulo no depende de Django: recibe cadenas y enteros y devuelve
estructuras de datos sencillas. Así se puede probar por separado de las
vistas y usar también desde la consola:

    >>> from representacion.converters import convertir, analizar_texto
    >>> convertir("FF", 16).binario
    '11111111'
    >>> analizar_texto("Año").total_bytes
    4

Las conversiones entre bases se programan a mano (método de Horner para
pasar a decimal y divisiones sucesivas para pasar del decimal a otra base)
para que se vea el algoritmo; las pruebas comparan el resultado con las
funciones integradas de Python (int y format).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

BASES = {2: "binario", 8: "octal", 10: "decimal", 16: "hexadecimal"}
DIGITOS = "0123456789ABCDEF"
PREFIJOS = {2: "0B", 8: "0O", 16: "0X"}
DIGITOS_PERMITIDOS = {
    2: "0 y 1",
    8: "del 0 al 7",
    10: "del 0 al 9",
    16: "del 0 al 9 y letras de la A a la F",
}
SEPARADORES = " _"

VALOR_MAXIMO = 65_535  # 2**16 - 1: el mayor entero sin signo de 16 bits
BITS_POR_BYTE = 8
LONGITUD_MAXIMA_ENTRADA = 40
LONGITUD_MAXIMA_TEXTO = 20


class ErrorValidacion(ValueError):
    """Dato no válido. «mensaje» está redactado para mostrarse al usuario."""

    def __init__(self, mensaje: str, codigo: str):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def formatear_miles(numero: int) -> str:
    """Separa los miles con un espacio duro, como recomienda la RAE: 65535 → «65 535»."""
    if numero < 10_000:
        return str(numero)
    return f"{numero:,}".replace(",", " ")


# ---------------------------------------------------------------------------
# Sistemas numéricos
# ---------------------------------------------------------------------------


def validar_base(base: int) -> int:
    if base not in BASES:
        raise ErrorValidacion(f"La base {base} no es válida. Elija 2, 8, 10 o 16.", "base_invalida")
    return base


def limpiar_entrada(entrada: str | None) -> str:
    """Comprobaciones que no dependen de la base: vacío, signo y longitud."""
    texto = (entrada or "").strip()
    if not texto:
        raise ErrorValidacion("La entrada está vacía. Escriba un número.", "vacio")
    if texto.startswith("-"):
        raise ErrorValidacion(
            f"No se admiten valores negativos («{texto}»). "
            f"Escriba un número entre 0 y {formatear_miles(VALOR_MAXIMO)}.",
            "negativo",
        )
    if len(texto) > LONGITUD_MAXIMA_ENTRADA:
        raise ErrorValidacion(
            f"La entrada es demasiado larga ({len(texto)} caracteres); "
            f"el máximo es {LONGITUD_MAXIMA_ENTRADA}.",
            "demasiado_larga",
        )
    return texto


def normalizar_digitos(entrada: str, base: int) -> str:
    """Devuelve solo los dígitos, en mayúsculas, tras comprobar que son de la base.

    Se aceptan el prefijo propio de la base (0b, 0o, 0x) y espacios o guiones
    bajos para agrupar dígitos, como en «1111 0000» o «0xFF_FF».
    """
    validar_base(base)
    texto = limpiar_entrada(entrada)
    prefijo = PREFIJOS.get(base)
    if prefijo and texto.upper().startswith(prefijo):
        texto = texto[len(prefijo):]
    digitos = "".join(caracter for caracter in texto if caracter not in SEPARADORES)
    if not digitos:
        raise ErrorValidacion("Falta el número: solo se escribió un prefijo o separadores.", "vacio")

    # Conjunto de caracteres sueltos: «in» sobre la cadena DIGITOS aceptaría
    # subcadenas, y algunas letras se convierten en dos al pasar a mayúscula.
    permitidos = set(DIGITOS[:base])
    for caracter in digitos:
        if caracter.upper() not in permitidos:
            raise ErrorValidacion(
                f"«{caracter}» no es un dígito válido en base {base} ({BASES[base]}). "
                f"Use solo dígitos {DIGITOS_PERMITIDOS[base]}.",
                "digito_invalido",
            )
    return digitos.upper()


def a_decimal(digitos: str, base: int) -> int:
    """Método de Horner: «1A» en base 16 → (0·16 + 1)·16 + 10 = 26."""
    valor = 0
    for caracter in digitos:
        valor = valor * base + DIGITOS.index(caracter)
    return valor


def desde_decimal(valor: int, base: int) -> str:
    """Divisiones sucesivas: los restos, leídos del último al primero, son los dígitos."""
    if valor < 0:
        raise ValueError("Solo se convierten enteros sin signo.")
    if valor == 0:
        return "0"
    digitos = []
    while valor > 0:
        valor, resto = divmod(valor, base)
        digitos.append(DIGITOS[resto])
    return "".join(reversed(digitos))


def bits_significativos(valor: int) -> int:
    """Bits necesarios sin ceros a la izquierda. Por convención, el 0 ocupa 1 bit."""
    return max(1, valor.bit_length())


def bytes_necesarios(valor: int) -> int:
    """Bytes enteros que hacen falta para guardar el valor (división redondeada hacia arriba)."""
    return (bits_significativos(valor) + BITS_POR_BYTE - 1) // BITS_POR_BYTE


def binario_relleno(valor: int) -> str:
    """Binario con ceros a la izquierda hasta un múltiplo de 8 bits: 5 → «00000101»."""
    return desde_decimal(valor, 2).zfill(bytes_necesarios(valor) * BITS_POR_BYTE)


@dataclass(frozen=True)
class ResultadoConversion:
    entrada: str  # lo que escribió el usuario, sin espacios a los lados
    base_origen: int
    digitos: str  # la entrada normalizada: sin prefijo ni separadores
    valor: int
    decimal: str
    binario: str  # relleno hasta completar bytes
    octal: str
    hexadecimal: str
    bits_significativos: int
    bytes_necesarios: int

    @property
    def nombre_base(self) -> str:
        return BASES[self.base_origen]

    @property
    def bits_totales(self) -> int:
        return len(self.binario)

    @property
    def bits_relleno(self) -> int:
        return self.bits_totales - self.bits_significativos

    @property
    def grupos_de_bytes(self) -> list[str]:
        return [self.binario[i:i + BITS_POR_BYTE] for i in range(0, len(self.binario), BITS_POR_BYTE)]

    @property
    def binario_agrupado(self) -> str:
        return " ".join(self.grupos_de_bytes)

    @property
    def bytes_detalle(self) -> list[dict]:
        """Cada byte con sus bits marcados como significativos o de relleno."""
        detalle = []
        for indice, grupo in enumerate(self.grupos_de_bytes):
            bits = []
            for posicion, bit in enumerate(grupo, start=indice * BITS_POR_BYTE):
                bits.append((bit, posicion < self.bits_relleno))
            detalle.append({"bits": bits, "hex": desde_decimal(a_decimal(grupo, 2), 16).zfill(2)})
        return detalle

    @property
    def desarrollo_posicional(self) -> list[dict]:
        """Términos dígito × base^posición distintos de cero: «FF» → 15·16¹ + 15·16⁰."""
        terminos = []
        for exponente, caracter in enumerate(reversed(self.digitos)):
            valor_digito = DIGITOS.index(caracter)
            if valor_digito:
                terminos.append({
                    "digito": caracter,
                    "valor_digito": valor_digito,
                    "exponente": exponente,
                    "valor": valor_digito * self.base_origen ** exponente,
                })
        return list(reversed(terminos))


def convertir(entrada: str, base: int) -> ResultadoConversion:
    """Valida la entrada y la expresa en las cuatro bases."""
    digitos = normalizar_digitos(entrada, base)
    valor = a_decimal(digitos, base)
    if valor > VALOR_MAXIMO:
        raise ErrorValidacion(
            f"«{entrada.strip()}» en base {base} equivale a {formatear_miles(valor)}, que está fuera de rango: "
            f"el valor debe estar entre 0 y {formatear_miles(VALOR_MAXIMO)} (16 bits sin signo).",
            "fuera_de_rango",
        )
    return ResultadoConversion(
        entrada=entrada.strip(),
        base_origen=base,
        digitos=digitos,
        valor=valor,
        decimal=desde_decimal(valor, 10),
        binario=binario_relleno(valor),
        octal=desde_decimal(valor, 8),
        hexadecimal=desde_decimal(valor, 16),
        bits_significativos=bits_significativos(valor),
        bytes_necesarios=bytes_necesarios(valor),
    )


# ---------------------------------------------------------------------------
# Caracteres y UTF-8
# ---------------------------------------------------------------------------

NOMBRES_ESPECIALES = {
    " ": "(espacio)",
    "\t": "(tabulador)",
    " ": "(espacio duro)",
}


@dataclass(frozen=True)
class InfoCaracter:
    caracter: str

    @property
    def codigo(self) -> int:
        return ord(self.caracter)

    @property
    def punto_codigo(self) -> str:
        return f"U+{self.codigo:04X}"

    @property
    def hexadecimal(self) -> str:
        return f"0x{self.codigo:02X}"

    @property
    def bytes_utf8(self) -> bytes:
        return self.caracter.encode("utf-8")

    @property
    def utf8_hex(self) -> str:
        return " ".join(f"{byte:02X}" for byte in self.bytes_utf8)

    @property
    def utf8_binario(self) -> str:
        return " ".join(format(byte, "08b") for byte in self.bytes_utf8)

    @property
    def num_bytes(self) -> int:
        return len(self.bytes_utf8)

    @property
    def visible(self) -> str:
        """Cómo mostrar el carácter en una tabla aunque sea invisible o combinable."""
        if self.caracter in NOMBRES_ESPECIALES:
            return NOMBRES_ESPECIALES[self.caracter]
        if unicodedata.combining(self.caracter):
            return "◌" + self.caracter  # ◌ como soporte del diacrítico
        if not self.caracter.isprintable():
            return "(no imprimible)"
        return self.caracter


@dataclass(frozen=True)
class AnalisisTexto:
    texto: str
    caracteres: tuple[InfoCaracter, ...]

    @property
    def total_caracteres(self) -> int:
        return len(self.texto)

    @property
    def bytes_utf8(self) -> bytes:
        return self.texto.encode("utf-8")

    @property
    def total_bytes(self) -> int:
        return len(self.bytes_utf8)

    @property
    def utf8_hex(self) -> str:
        return " ".join(f"{byte:02X}" for byte in self.bytes_utf8)

    @property
    def es_ascii(self) -> bool:
        return self.texto.isascii()

    @property
    def literal_python(self) -> str:
        """Cómo escribe Python el texto en la consola: 'Año'."""
        return repr(self.texto)

    @property
    def literal_bytes(self) -> str:
        """Cómo escribe Python los bytes UTF-8: b'A\\xc3\\xb1o'."""
        return repr(self.bytes_utf8)


def validar_texto(texto: str | None) -> str:
    texto = texto or ""
    if not texto.strip():
        raise ErrorValidacion("El texto está vacío. Escriba al menos un carácter.", "texto_vacio")
    if len(texto) > LONGITUD_MAXIMA_TEXTO:
        raise ErrorValidacion(
            f"El texto tiene {len(texto)} caracteres y el máximo es {LONGITUD_MAXIMA_TEXTO}. "
            "Acórtelo e inténtelo de nuevo.",
            "texto_largo",
        )
    return texto


def analizar_texto(texto: str) -> AnalisisTexto:
    """Describe cada carácter (punto de código Unicode) y sus bytes en UTF-8."""
    texto = validar_texto(texto)
    return AnalisisTexto(texto=texto, caracteres=tuple(InfoCaracter(c) for c in texto))
