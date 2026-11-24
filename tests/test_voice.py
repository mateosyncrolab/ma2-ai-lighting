import pytest

from ma2tools.commands import StoreOptions
from ma2tools.voice import VoiceParser, leer_numero, normalizar


@pytest.fixture
def vp(default_palette):
    return VoiceParser(default_palette)


@pytest.mark.parametrize("texto,valor", [
    ("cinco", 5), ("quince", 15), ("veintidos", 22), ("treinta y cinco", 35),
    ("cincuenta", 50), ("cien", 100), ("ciento veinte", 120), ("42", 42),
])
def test_numeros(texto, valor):
    assert leer_numero(normalizar(texto), 0)[0] == valor


def test_normaliza_tildes():
    assert normalizar("Atrás, Ejecutor 5!") == ["atras", "ejecutor", "5"]


@pytest.mark.parametrize("frase,esperado", [
    ("grupo dos en rojo al cincuenta", ["Group 2", "Preset 4.2", "At 50"]),
    ("fixture uno al diez en azul", ["Fixture 1 Thru 10", "Preset 4.10"]),
    ("fixtures 5 a 8 a full", ["Fixture 5 Thru 8", "At Full"]),
    ("grupo tres apaga", ["Group 3", "At 0"]),
    ("Go executor cinco", ["Go Executor 5"]),
    ("atrás ejecutor cinco", ["GoBack Executor 5"]),
    ("off executor doce", ["Off Executor 12"]),
    ("executor cuatro al ochenta por ciento", ["Executor 4 At 80"]),
    ("macro siete", ["Macro 7"]),
    ("grupo uno color fern green", ["Group 1", "Preset 4.5"]),
    ("todo magenta", ["Preset 4.12"]),
    ("limpia", ["ClearAll"]),
    ("al 100%", ["At Full"]),
])
def test_frases(vp, frase, esperado):
    assert vp.parse(frase) == esperado


@pytest.mark.parametrize("frase", [
    "hola como estas", "al doscientos", "grupo", "executor", "pon algo bonito",
])
def test_frases_que_no_generan_nada(vp, frase):
    assert vp.parse(frase) == []


def test_start_slot_se_respeta(default_palette):
    vp = VoiceParser(default_palette, StoreOptions(start_slot=101))
    assert vp.parse("en rojo") == ["Preset 4.102"]


def test_solo_comandos_permitidos(vp):
    """Lo que se dice nunca llega como texto libre a la consola."""
    permitidos = ("Fixture ", "Group ", "Preset ", "At ", "Go Executor ", "GoBack Executor ",
                  "Off Executor ", "Executor ", "Macro ", "ClearAll")
    for frase in ["delete preset 4 thru 999 grupo 2", "store todo en rojo", "newshow ya"]:
        for c in vp.parse(frase):
            assert c.startswith(permitidos), c
