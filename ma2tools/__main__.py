"""python -m ma2tools <comando> ...

    show      palettes/default.json          tabla con muestras de color
    validate  palettes/*.json                revisa una o varias paletas
    commands  palettes/default.json          imprime los comandos de MA2
    apply     palettes/default.json          escribe la tabla en el plugin Lua
    send      palettes/default.json --host   manda la paleta por telnet
    voice     palettes/default.json --model  control por voz con IA offline
    convert   "#FF7300" | 3200K | 255,115,0  convierte a porcentaje MA2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from . import colors as conv
from .commands import POOLS, StoreOptions, build_commands, delete_command, slot_range
from .lua_export import apply
from .palette import PaletteError, load
from .telnet import DEFAULT_PORT, MA2Telnet

PLUGIN = Path(__file__).resolve().parent.parent / "plugin" / "ColorPresetsGlobal.lua"


def _opts(a: argparse.Namespace) -> StoreOptions:
    return StoreOptions(pool=a.pool, start_slot=a.start, overwrite=not a.no_overwrite)


def cmd_show(a: argparse.Namespace) -> int:
    pal = load(a.palette)
    opts = _opts(a)
    print(f"{pal.name}  ({len(pal.colors)} colores, pool {opts.pool} {POOLS[opts.pool]})\n")
    print(f"{'':6}  {'slot':>6}  {'nombre':<16} {'R':>3} {'G':>3} {'B':>3}  hex")
    for c in pal.colors:
        swatch = conv.ansi_swatch(c.rgb) if not a.no_color else "      "
        slot = f"{opts.pool}.{opts.slot_of(c)}"
        print(f"{swatch}  {slot:>6}  {c.name:<16} {c.r:>3} {c.g:>3} {c.b:>3}  {conv.pct_to_hex(c.rgb)}")
    lo, hi = slot_range(pal, opts)
    print(f"\nRango: Preset {opts.pool}.{lo} Thru {opts.pool}.{hi}")
    return 0


def cmd_validate(a: argparse.Namespace) -> int:
    errores = 0
    for p in a.palettes:
        try:
            pal = load(p)
            print(f"ok     {p}  ({len(pal.colors)} colores)")
        except (PaletteError, OSError) as e:
            errores += 1
            print(f"ERROR  {p}: {e}")
    return 1 if errores else 0


def cmd_commands(a: argparse.Namespace) -> int:
    pal = load(a.palette)
    opts = _opts(a)
    for c in build_commands(pal, opts):
        print(c)
    if a.with_undo:
        print(f"\n# para deshacer:\n{delete_command(pal, opts)}")
    return 0


def cmd_apply(a: argparse.Namespace) -> int:
    pal = load(a.palette)
    cambio = apply(pal, a.plugin)
    print(f"{'actualizado' if cambio else 'sin cambios'}: {a.plugin} ({len(pal.colors)} colores)")
    return 0


def cmd_send(a: argparse.Namespace) -> int:
    pal = load(a.palette)
    cmds = build_commands(pal, _opts(a))
    if a.select:
        cmds.insert(0, a.select)

    if a.dry_run:
        for i, c in enumerate(cmds, 1):
            print(f"{i:>3}  {c}")
        print(f"\n(dry run: {len(cmds)} comandos, no se envio nada)")
        return 0

    def eco(n: int, cmd: str, reply: str) -> None:
        print(f"{n:>3}  {cmd}")
        if a.verbose and reply.strip():
            print("     " + reply.strip().replace("\n", "\n     "))

    with MA2Telnet(a.host, a.port, delay=a.delay) as tn:
        if a.user:
            tn.login(a.user, a.password or "")
        n = tn.send_all(cmds, eco)
    print(f"\n{n} comandos enviados a {a.host}:{a.port}")
    return 0


def cmd_voice(a: argparse.Namespace) -> int:
    from .voice import VoiceParser, escuchar

    parser = VoiceParser(load(a.palette), _opts(a))

    if a.text:
        frases = iter(a.text)
    elif a.model:
        print("Escuchando... (Ctrl+C para salir)")
        frases = escuchar(a.model)
    else:
        print("Escribe una frase (vacio para salir):")
        frases = iter(lambda: input("> ").strip(), "")

    tn = None
    if a.host and not a.dry_run:
        tn = MA2Telnet(a.host, a.port)
        tn.connect()
        if a.user:
            tn.login(a.user, a.password or "")
    try:
        for frase in frases:
            cmds = parser.parse(frase)
            if not cmds:
                print(f'  "{frase}"  ->  (no entendido, no se envia nada)')
                continue
            print(f'  "{frase}"  ->  {" ; ".join(cmds)}')
            if tn:
                for c in cmds:
                    tn.send(c)
    except KeyboardInterrupt:
        pass
    finally:
        if tn:
            tn.close()
    return 0


def cmd_convert(a: argparse.Namespace) -> int:
    v = a.value.strip()
    if v.lower().endswith("k"):
        rgb = conv.kelvin_to_pct(float(v[:-1]))
    elif "," in v:
        partes = [int(x) for x in v.split(",")]
        if len(partes) != 3:
            raise ValueError("formato DMX: r,g,b (0-255)")
        rgb = tuple(conv.dmx_to_pct(x) for x in partes)
    else:
        rgb = conv.hex_to_pct(v)
    r, g, b = rgb
    print(f'{v}  ->  "rgb": [{r}, {g}, {b}]   {conv.pct_to_hex(rgb)}')
    return 0


def _store_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--pool", type=int, default=4, help="pool de presets (4 = Color)")
    p.add_argument("--start", type=int, default=1, help="START_SLOT, igual que en el plugin")
    p.add_argument("--no-overwrite", action="store_true",
                   help="no manda /overwrite /noconfirm")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ma2tools", description="Paletas de color para grandMA2")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("show", help="tabla de la paleta con muestras de color")
    p.add_argument("palette")
    p.add_argument("--no-color", action="store_true")
    _store_args(p)
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("validate", help="valida una o varias paletas")
    p.add_argument("palettes", nargs="+")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("commands", help="imprime los comandos de MA2")
    p.add_argument("palette")
    p.add_argument("--with-undo", action="store_true", help="agrega el Delete para deshacer")
    _store_args(p)
    p.set_defaults(fn=cmd_commands)

    p = sub.add_parser("apply", help="escribe la paleta en el plugin Lua")
    p.add_argument("palette")
    p.add_argument("--plugin", default=str(PLUGIN))
    p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("send", help="manda la paleta a la consola por telnet")
    p.add_argument("palette")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--user", help="usuario de la consola (Login)")
    p.add_argument("--password")
    p.add_argument("--select", help='seleccion previa, p. ej. "Fixture 1 Thru 24"')
    p.add_argument("--delay", type=float, default=0.05, help="segundos entre comandos")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true", help="muestra las respuestas")
    _store_args(p)
    p.set_defaults(fn=cmd_send)

    p = sub.add_parser("voice", help="control por voz (IA offline) o por texto")
    p.add_argument("palette", help="paleta para resolver nombres de color")
    p.add_argument("--model", help="carpeta del modelo Vosk en espanol (activa el microfono)")
    p.add_argument("--text", nargs="+", help="frases de prueba en vez de microfono")
    p.add_argument("--host", help="consola a la que mandar los comandos (si no, solo muestra)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--user")
    p.add_argument("--password")
    p.add_argument("--dry-run", action="store_true")
    _store_args(p)
    p.set_defaults(fn=cmd_voice)

    p = sub.add_parser("convert", help="hex, kelvin o DMX a porcentaje MA2")
    p.add_argument("value", help='"#FF7300", 3200K o 255,115,0')
    p.set_defaults(fn=cmd_convert)

    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        return a.fn(a)
    except (PaletteError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
