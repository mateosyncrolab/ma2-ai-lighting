import json

import pytest

from ma2tools.palette import PaletteError, load, parse


def test_default_carga(default_palette):
    assert len(default_palette.colors) == 10
    assert default_palette.colors[1].name == "Red"
    assert default_palette.colors[1].rgb == (100, 0, 0)


def test_hex_y_kelvin():
    pal = parse({"colors": [
        {"num": 1, "name": "Ambar", "hex": "#FFBF00"},
        {"num": 2, "name": "Tungsteno", "kelvin": 3200},
    ]})
    assert pal.colors[0].rgb == (100, 75, 0)
    assert pal.colors[1].r == 100


@pytest.mark.parametrize("color,mensaje", [
    ({"name": "X", "rgb": [1, 2, 3]}, "num"),
    ({"num": 0, "name": "X", "rgb": [1, 2, 3]}, "num"),
    ({"num": 1, "rgb": [1, 2, 3]}, "name"),
    ({"num": 1, "name": 'Rojo "fuerte"', "rgb": [1, 2, 3]}, "comillas"),
    ({"num": 1, "name": "X"}, "exactamente uno"),
    ({"num": 1, "name": "X", "rgb": [1, 2, 3], "hex": "#fff"}, "exactamente uno"),
    ({"num": 1, "name": "X", "rgb": [1, 2]}, "rgb"),
    ({"num": 1, "name": "X", "rgb": [255, 0, 0]}, "0..100"),
    ({"num": 1, "name": "X", "hex": "zzz"}, "hex"),
])
def test_colores_invalidos(color, mensaje):
    with pytest.raises(PaletteError, match=mensaje):
        parse({"colors": [color]})


def test_num_repetido():
    with pytest.raises(PaletteError, match="repetido"):
        parse({"colors": [
            {"num": 1, "name": "A", "rgb": [0, 0, 0]},
            {"num": 1, "name": "B", "rgb": [0, 0, 0]},
        ]})


def test_paleta_vacia():
    with pytest.raises(PaletteError):
        parse({"colors": []})


def test_json_roto(tmp_path):
    p = tmp_path / "rota.json"
    p.write_text("{ colors: ", encoding="utf-8")
    with pytest.raises(PaletteError, match="JSON"):
        load(p)


def test_todas_las_paletas_del_repo_son_validas():
    from conftest import RAIZ
    for f in (RAIZ / "palettes").glob("*.json"):
        assert parse(json.loads(f.read_text(encoding="utf-8"))).colors
