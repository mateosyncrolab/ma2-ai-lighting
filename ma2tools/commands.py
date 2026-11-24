"""Genera la secuencia de comandos de MA2 para una paleta.

Produce exactamente lo mismo que build_commands() en el plugin Lua, para poder
mandarlo por telnet sin pasar por el Plugin Pool. tests/test_plugin_lua.py
comprueba que las dos implementaciones no se separen.
"""

from __future__ import annotations

from dataclasses import dataclass

from .palette import Color, Palette

ATTR_R = "ColorRGB1"
ATTR_G = "ColorRGB2"
ATTR_B = "ColorRGB3"

POOLS = {
    0: "All", 1: "Dimmer", 2: "Position", 3: "Gobo", 4: "Color",
    5: "Beam", 6: "Focus", 7: "Control", 8: "Shapers", 9: "Video",
}


@dataclass(frozen=True)
class StoreOptions:
    pool: int = 4
    start_slot: int = 1
    overwrite: bool = True

    def __post_init__(self) -> None:
        if self.pool not in POOLS:
            raise ValueError(f"pool invalido: {self.pool} (0-9)")
        if self.start_slot < 1:
            raise ValueError("start_slot tiene que ser >= 1")

    def slot_of(self, color: Color) -> int:
        return self.start_slot - 1 + color.num

    def suffix(self) -> str:
        return " /global /overwrite /noconfirm" if self.overwrite else " /global"


def build_commands(palette: Palette, opts: StoreOptions = StoreOptions()) -> list[str]:
    cmds: list[str] = []
    for c in palette.colors:
        target = f"Preset {opts.pool}.{opts.slot_of(c)}"
        cmds += [
            f'Attribute "{ATTR_R}" At {c.r}',
            f'Attribute "{ATTR_G}" At {c.g}',
            f'Attribute "{ATTR_B}" At {c.b}',
            f"Store {target}{opts.suffix()}",
            f'Label {target} "{c.name}"',
        ]
    cmds.append("ClearAll")
    return cmds


def slot_range(palette: Palette, opts: StoreOptions) -> tuple[int, int]:
    slots = [opts.slot_of(c) for c in palette.colors]
    return min(slots), max(slots)


def delete_command(palette: Palette, opts: StoreOptions) -> str:
    lo, hi = slot_range(palette, opts)
    return f"Delete Preset {opts.pool}.{lo} Thru {opts.pool}.{hi}"
