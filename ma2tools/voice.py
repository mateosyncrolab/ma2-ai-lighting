"""Control por voz: frases en espanol -> comandos de grandMA2.

El reconocimiento de voz (Vosk, offline) convierte el audio en texto y este
modulo traduce ese texto a comandos. La traduccion es determinista y cerrada:
solo puede producir los comandos de la lista de abajo, nunca pasa texto libre
a la consola. En un show en vivo eso importa mas que entender cualquier frase.

Frases que entiende (se pueden combinar en una sola):

    "fixture uno al diez"         -> Fixture 1 Thru 10
    "grupo tres"                  -> Group 3
    "en rojo" / "color azul"      -> Preset 4.<slot del color en la paleta>
    "al cincuenta" / "a full"     -> At 50 / At Full
    "apaga"                       -> At 0
    "go executor cinco"           -> Go Executor 5
    "atras executor cinco"        -> GoBack Executor 5
    "off executor cinco"          -> Off Executor 5
    "executor cinco al ochenta"   -> Executor 5 At 80
    "macro dos"                   -> Macro 2
    "limpia" / "clear"            -> ClearAll
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterator

from .commands import StoreOptions
from .palette import Palette

_UNIDADES = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "veintiun": 21, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
}
_DECENAS = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}
_CENTENAS = {
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300,
    "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600,
    "setecientos": 700, "ochocientos": 800, "novecientos": 900,
}
_NUMERICAS = set(_UNIDADES) | set(_DECENAS) | set(_CENTENAS) | {"y"}


def normalizar(texto: str) -> list[str]:
    """Minusculas, sin tildes ni puntuacion, separado en palabras."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"(\d)%", r"\1", t)
    return re.findall(r"[a-z]+|\d+", t)


def leer_numero(palabras: list[str], i: int) -> tuple[int, int] | None:
    """Lee un numero desde palabras[i]. Devuelve (valor, indice siguiente)."""
    if i >= len(palabras):
        return None
    if palabras[i].isdigit():
        return int(palabras[i]), i + 1

    total, j, leido = 0, i, False
    while j < len(palabras) and palabras[j] in _NUMERICAS:
        w = palabras[j]
        if w == "y":
            # "treinta y cinco": la y solo vale entre decena y unidad
            if not (leido and j + 1 < len(palabras) and palabras[j + 1] in _UNIDADES):
                break
        elif w in _CENTENAS:
            total += _CENTENAS[w]
        elif w in _DECENAS:
            total += _DECENAS[w]
        else:
            total += _UNIDADES[w]
        leido = leido or w != "y"
        j += 1
    return (total, j) if leido else None


_SINONIMOS_COLOR = {
    "blanco": "white", "rojo": "red", "naranja": "orange", "amarillo": "yellow",
    "verde": "green", "cian": "cyan", "azul": "blue", "violeta": "violet",
    "morado": "violet", "magenta": "magenta", "rosado": "magenta",
}


class VoiceParser:
    def __init__(self, palette: Palette, opts: StoreOptions = StoreOptions()) -> None:
        self.opts = opts
        self._colores: dict[str, int] = {}
        for c in palette.colors:
            self._colores[" ".join(normalizar(c.name))] = opts.slot_of(c)

    def _color(self, palabras: list[str], i: int) -> tuple[int, int] | None:
        # primero nombres de varias palabras ("fern green")
        for largo in (3, 2, 1):
            frase = " ".join(palabras[i:i + largo])
            if frase in self._colores:
                return self._colores[frase], i + largo
        w = palabras[i]
        if w in _SINONIMOS_COLOR and _SINONIMOS_COLOR[w] in self._colores:
            return self._colores[_SINONIMOS_COLOR[w]], i + 1
        return None

    def parse(self, texto: str) -> list[str]:
        return list(self._tokens(normalizar(texto)))

    def _tokens(self, p: list[str]) -> Iterator[str]:
        i = 0
        while i < len(p):
            w = p[i]

            if w in ("limpia", "limpiar", "clear"):
                yield "ClearAll"
                i += 1
                continue

            if w in ("apaga", "apagar", "apagalo"):
                yield "At 0"
                i += 1
                continue

            if w in ("fixture", "fixtures", "aparato", "aparatos"):
                a = leer_numero(p, i + 1)
                if a:
                    desde, j = a
                    if j < len(p) and p[j] in ("al", "a", "hasta", "thru"):
                        b = leer_numero(p, j + 1)
                        if b:
                            yield f"Fixture {desde} Thru {b[0]}"
                            i = b[1]
                            continue
                    yield f"Fixture {desde}"
                    i = j
                    continue

            if w in ("grupo", "group"):
                n = leer_numero(p, i + 1)
                if n:
                    yield f"Group {n[0]}"
                    i = n[1]
                    continue

            if w == "macro":
                n = leer_numero(p, i + 1)
                if n:
                    yield f"Macro {n[0]}"
                    i = n[1]
                    continue

            accion = {"go": "Go", "dale": "Go", "atras": "GoBack", "back": "GoBack",
                      "off": "Off"}.get(w)
            sig = i + 1 if accion else i
            if sig < len(p) and p[sig] in ("executor", "ejecutor"):
                n = leer_numero(p, sig + 1)
                if n:
                    num, j = n
                    if accion:
                        yield f"{accion} Executor {num}"
                        i = j
                        continue
                    nivel = self._nivel(p, j)
                    if nivel:
                        yield f"Executor {num} At {nivel[0]}"
                        i = nivel[1]
                        continue
                    yield f"Go Executor {num}"
                    i = j
                    continue

            if w in ("en", "color", "de"):
                if i + 1 < len(p):
                    c = self._color(p, i + 1)
                    if c:
                        yield f"Preset {self.opts.pool}.{c[0]}"
                        i = c[1]
                        continue

            c = self._color(p, i)
            if c:
                yield f"Preset {self.opts.pool}.{c[0]}"
                i = c[1]
                continue

            nivel = self._nivel(p, i)
            if nivel:
                yield f"At {nivel[0]}"
                i = nivel[1]
                continue

            i += 1

    def _nivel(self, p: list[str], i: int) -> tuple[str, int] | None:
        """'al 50', 'a full', 'a cincuenta por ciento' -> ('50', siguiente)."""
        if i >= len(p) or p[i] not in ("al", "a", "intensidad", "dimmer"):
            return None
        j = i + 1
        if j < len(p) and p[j] in ("full", "tope", "maximo"):
            return "Full", j + 1
        n = leer_numero(p, j)
        if not n:
            return None
        valor, j = n
        if j + 1 < len(p) and p[j] == "por" and p[j + 1] == "ciento":
            j += 2
        if not 0 <= valor <= 100:
            return None
        return ("Full" if valor == 100 else str(valor)), j


def escuchar(model_path: str, samplerate: int = 16000) -> Iterator[str]:
    """Frases reconocidas desde el microfono con Vosk (offline).

    Requiere: pip install vosk sounddevice, y un modelo en espanol, p. ej.
    vosk-model-small-es-0.42 de https://alphacephei.com/vosk/models
    """
    import json
    import queue

    import sounddevice as sd
    from vosk import KaldiRecognizer, Model

    cola: "queue.Queue[bytes]" = queue.Queue()

    def callback(indata, frames, tiempo, status) -> None:
        cola.put(bytes(indata))

    rec = KaldiRecognizer(Model(model_path), samplerate)
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        while True:
            if rec.AcceptWaveform(cola.get()):
                texto = json.loads(rec.Result()).get("text", "").strip()
                if texto:
                    yield texto
