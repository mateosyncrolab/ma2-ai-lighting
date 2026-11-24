"""Escribe la tabla COLORS del plugin a partir de una paleta JSON.

Solo reemplaza lo que hay entre los marcadores `-- @palette-begin` y
`-- @palette-end`; el resto del plugin no se toca.
"""

from __future__ import annotations

from pathlib import Path

from .palette import Palette

BEGIN = "-- @palette-begin"
END = "-- @palette-end"


def lua_table(palette: Palette) -> str:
    ancho = max(len(c.name) for c in palette.colors) + 3  # comillas + coma
    filas = []
    for c in palette.colors:
        nombre = f'"{c.name}",'
        filas.append(
            f"  {{ num = {c.num:>2}, name = {nombre:<{ancho}} "
            f"r = {c.r:>3}, g = {c.g:>3}, b = {c.b:>3} }},"
        )
    return "local COLORS = {\n" + "\n".join(filas) + "\n}\n"


def apply(palette: Palette, plugin_path: str | Path) -> bool:
    """Reescribe la tabla en el plugin. Devuelve True si el archivo cambio."""
    path = Path(plugin_path)
    crudo = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in crudo else "\n"
    texto = crudo.replace("\r\n", "\n")

    if texto.count(BEGIN) != 1 or texto.count(END) != 1:
        raise ValueError(f"{path}: no encuentro los marcadores {BEGIN} / {END}")

    i = texto.index("\n", texto.index(BEGIN)) + 1
    j = texto.index(END)
    if j < i:
        raise ValueError(f"{path}: marcadores en orden incorrecto")

    nuevo = texto[:i] + lua_table(palette) + texto[j:]
    if nuevo == texto:
        return False
    path.write_bytes(nuevo.replace("\n", eol).encode("utf-8"))
    return True
