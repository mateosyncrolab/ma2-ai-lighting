"""Paletas de color en JSON.

Formato:

    {
      "name": "default",
      "colors": [
        {"num": 1, "name": "White", "rgb": [100, 100, 100]},
        {"num": 3, "name": "Orange", "hex": "#FF7300"},
        {"num": 20, "name": "Tungsten", "kelvin": 3200}
      ]
    }

Cada color se define con uno solo de: rgb (porcentaje 0..100), hex o kelvin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import colors as conv


class PaletteError(ValueError):
    pass


@dataclass(frozen=True)
class Color:
    num: int
    name: str
    r: int
    g: int
    b: int

    @property
    def rgb(self) -> conv.RGB:
        return self.r, self.g, self.b


@dataclass(frozen=True)
class Palette:
    name: str
    colors: tuple[Color, ...]


def _parse_color(raw: dict, index: int) -> Color:
    where = f"color #{index + 1}"
    if not isinstance(raw, dict):
        raise PaletteError(f"{where}: tiene que ser un objeto")

    num = raw.get("num")
    if not isinstance(num, int) or isinstance(num, bool) or num < 1:
        raise PaletteError(f"{where}: 'num' tiene que ser un entero >= 1")

    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise PaletteError(f"{where}: falta 'name'")
    if '"' in name:
        # el nombre va entre comillas en el comando Label
        raise PaletteError(f"{where}: el nombre no puede llevar comillas dobles")

    fuentes = [k for k in ("rgb", "hex", "kelvin") if k in raw]
    if len(fuentes) != 1:
        raise PaletteError(f"{where} ({name}): define exactamente uno de rgb, hex o kelvin")

    try:
        if "rgb" in raw:
            rgb = raw["rgb"]
            if (not isinstance(rgb, list) or len(rgb) != 3
                    or not all(isinstance(c, int) and not isinstance(c, bool) for c in rgb)):
                raise PaletteError(f"{where} ({name}): 'rgb' tiene que ser [r, g, b] enteros")
            if not all(0 <= c <= 100 for c in rgb):
                raise PaletteError(f"{where} ({name}): rgb va en porcentaje 0..100")
            r, g, b = rgb
        elif "hex" in raw:
            r, g, b = conv.hex_to_pct(str(raw["hex"]))
        else:
            r, g, b = conv.kelvin_to_pct(float(raw["kelvin"]))
    except ValueError as e:
        if isinstance(e, PaletteError):
            raise
        raise PaletteError(f"{where} ({name}): {e}") from None

    return Color(num=num, name=name.strip(), r=r, g=g, b=b)


def parse(data: dict) -> Palette:
    if not isinstance(data, dict) or not isinstance(data.get("colors"), list):
        raise PaletteError("la paleta necesita una lista 'colors'")
    if not data["colors"]:
        raise PaletteError("la paleta esta vacia")

    cols = tuple(_parse_color(c, i) for i, c in enumerate(data["colors"]))

    vistos: dict[int, str] = {}
    for c in cols:
        if c.num in vistos:
            raise PaletteError(f"num {c.num} repetido ({vistos[c.num]} y {c.name})")
        vistos[c.num] = c.name

    return Palette(name=str(data.get("name", "palette")), colors=cols)


def load(path: str | Path) -> Palette:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PaletteError(f"{path}: JSON invalido ({e})") from None
    return parse(data)
