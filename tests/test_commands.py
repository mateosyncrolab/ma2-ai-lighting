import pytest

from ma2tools.commands import StoreOptions, build_commands, delete_command, slot_range
from ma2tools.lua_export import apply, lua_table


def test_secuencia_de_un_color(default_palette):
    cmds = build_commands(default_palette)
    assert cmds[5:10] == [
        'Attribute "ColorRGB1" At 100',
        'Attribute "ColorRGB2" At 0',
        'Attribute "ColorRGB3" At 0',
        "Store Preset 4.2 /global /overwrite /noconfirm",
        'Label Preset 4.2 "Red"',
    ]
    assert cmds[-1] == "ClearAll"
    assert len(cmds) == 10 * 5 + 1


def test_start_slot_desplaza(default_palette):
    opts = StoreOptions(start_slot=101)
    assert "Store Preset 4.101 /global /overwrite /noconfirm" in build_commands(default_palette, opts)
    assert slot_range(default_palette, opts) == (101, 112)


def test_sin_overwrite(default_palette):
    cmds = build_commands(default_palette, StoreOptions(overwrite=False))
    assert "Store Preset 4.1 /global" in cmds
    assert not any("/noconfirm" in c for c in cmds)


def test_delete(default_palette):
    assert delete_command(default_palette, StoreOptions()) == "Delete Preset 4.1 Thru 4.12"


@pytest.mark.parametrize("kw", [{"pool": 10}, {"start_slot": 0}])
def test_opciones_invalidas(kw):
    with pytest.raises(ValueError):
        StoreOptions(**kw)


def test_apply_reproduce_el_plugin(default_palette, tmp_path):
    """La tabla generada desde default.json es la misma que trae el plugin."""
    from conftest import PLUGIN
    copia = tmp_path / "plugin.lua"
    copia.write_bytes(PLUGIN.read_bytes())
    assert apply(default_palette, copia) is False
    assert copia.read_bytes() == PLUGIN.read_bytes()


def test_apply_cambia_solo_la_tabla(default_palette, tmp_path):
    from conftest import PLUGIN
    from ma2tools.palette import parse
    copia = tmp_path / "plugin.lua"
    copia.write_bytes(PLUGIN.read_bytes())
    otra = parse({"colors": [{"num": 1, "name": "Ambar", "hex": "#FFBF00"}]})
    assert apply(otra, copia) is True
    texto = copia.read_text(encoding="utf-8")
    assert lua_table(otra).strip() in texto.replace("\r\n", "\n")
    assert '"Magenta"' not in texto
    assert "local PRESET_POOL = 4" in texto


def test_apply_sin_marcadores(default_palette, tmp_path):
    f = tmp_path / "x.lua"
    f.write_text("local COLORS = {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="marcadores"):
        apply(default_palette, f)
