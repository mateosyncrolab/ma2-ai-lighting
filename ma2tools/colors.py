"""Conversiones de color al formato que usa el command line de grandMA2.

MA2 trabaja los atributos de mezcla RGB (ColorRGB1..3) en porcentaje 0..100,
no en 0..255 como DMX crudo ni en hex como los editores de color.
"""

from __future__ import annotations

import math
import re

RGB = tuple[int, int, int]

_HEX = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def clamp_pct(value: float) -> int:
    return max(0, min(100, int(round(value))))


def dmx_to_pct(value: int) -> int:
    """0..255 (valor DMX de 8 bits) -> 0..100."""
    if not 0 <= value <= 255:
        raise ValueError(f"valor DMX fuera de rango: {value}")
    return clamp_pct(value * 100 / 255)


def pct_to_dmx(value: int) -> int:
    """0..100 -> 0..255."""
    if not 0 <= value <= 100:
        raise ValueError(f"porcentaje fuera de rango: {value}")
    return int(round(value * 255 / 100))


def hex_to_pct(code: str) -> RGB:
    """'#FF7300' o 'f70' -> (100, 45, 0)."""
    m = _HEX.match(code.strip())
    if not m:
        raise ValueError(f"color hex invalido: {code!r}")
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return dmx_to_pct(r), dmx_to_pct(g), dmx_to_pct(b)


def pct_to_hex(rgb: RGB) -> str:
    return "#" + "".join(f"{pct_to_dmx(c):02X}" for c in rgb)


def kelvin_to_pct(kelvin: float) -> RGB:
    """Temperatura de color (1000..40000 K) -> RGB aproximado en porcentaje.

    Aproximacion de Tanner Helland sobre los datos de cuerpo negro de Mitchell
    Charity. Sirve como punto de partida para blancos calidos/frios en fixtures
    RGB; para CTO/CTB exactos en fixtures con CTC hay que usar el atributo de
    temperatura de color de la libreria.
    """
    if not 1000 <= kelvin <= 40000:
        raise ValueError(f"temperatura fuera de rango (1000-40000 K): {kelvin}")
    t = kelvin / 100

    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661
    else:
        r = 329.698727446 * (t - 60) ** -0.1332047592
        g = 288.1221695283 * (t - 60) ** -0.0755148492

    if t >= 66:
        b = 255.0
    elif t <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(t - 10) - 305.0447927307

    return tuple(clamp_pct(max(0.0, min(255.0, c)) * 100 / 255) for c in (r, g, b))  # type: ignore[return-value]


def ansi_swatch(rgb: RGB, width: int = 6) -> str:
    """Bloque de color para terminales con truecolor."""
    r, g, b = (pct_to_dmx(c) for c in rgb)
    return f"\x1b[48;2;{r};{g};{b}m{' ' * width}\x1b[0m"
