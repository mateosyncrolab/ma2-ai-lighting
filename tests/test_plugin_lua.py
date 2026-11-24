"""Ejecuta el plugin Lua real contra una API gma simulada.

No hace falta consola: se reemplaza `gma` por funciones que registran lo que
el plugin intenta hacer.
"""

import pytest

lupa = pytest.importorskip("lupa")

from conftest import PLUGIN  # noqa: E402
from ma2tools.commands import build_commands  # noqa: E402

MOCK = """
CMDS, DIALOGS, ECHOS = {}, {}, {}
gma = {
  cmd = function(c) table.insert(CMDS, c); return nil end,
  echo = function(...) table.insert(ECHOS, table.concat({...}, " ")) end,
  feedback = function(...) end,
  gui = { confirm = function(t, m) table.insert(DIALOGS, m); return CONFIRM end },
  show = { getvar = function(v) if v == "SELECTEDFIXTURESCOUNT" then return SEL end end },
}
"""


def correr(sel: str, confirm: bool, src: str | None = None):
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    g = lua.globals()
    g.SEL = sel
    g.CONFIRM = confirm
    main = lua.execute(src or PLUGIN.read_text(encoding="utf-8"))
    main()
    lista = lambda t: [t[i] for i in range(1, len(t) + 1)]  # noqa: E731
    return lista(g.CMDS), lista(g.DIALOGS), lista(g.ECHOS)


def test_lua_y_python_generan_lo_mismo(default_palette):
    cmds, dialogs, _ = correr("12", True)
    assert cmds == build_commands(default_palette)
    assert "Fixtures seleccionados: 12" in dialogs[0]
    assert "Slots: 4.1 thru 4.12" in dialogs[0]


def test_sin_seleccion_no_toca_nada():
    cmds, dialogs, echos = correr("0", True)
    assert cmds == []
    assert "No hay fixtures seleccionados" in dialogs[0]
    assert any("abortado" in e for e in echos)


def test_cancelar_no_toca_nada():
    cmds, _, echos = correr("5", False)
    assert cmds == []
    assert any("cancelado" in e for e in echos)


def test_dry_run_no_ejecuta():
    src = PLUGIN.read_text(encoding="utf-8").replace(
        "local DRY_RUN = false", "local DRY_RUN = true")
    cmds, dialogs, _ = correr("5", True, src)
    assert cmds == []
    assert "DRY RUN" in dialogs[0]
