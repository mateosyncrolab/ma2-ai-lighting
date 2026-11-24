import pytest

from ma2tools import colors as conv


@pytest.mark.parametrize("dmx,pct", [(0, 0), (255, 100), (128, 50), (115, 45)])
def test_dmx_to_pct(dmx, pct):
    assert conv.dmx_to_pct(dmx) == pct


def test_hex_largo_y_corto():
    assert conv.hex_to_pct("#FF7300") == (100, 45, 0)
    assert conv.hex_to_pct("fff") == (100, 100, 100)
    assert conv.hex_to_pct("#000000") == (0, 0, 0)


@pytest.mark.parametrize("malo", ["#GG0000", "#12345", "", "rojo"])
def test_hex_invalido(malo):
    with pytest.raises(ValueError):
        conv.hex_to_pct(malo)


def test_hex_ida_y_vuelta():
    for rgb in [(100, 0, 0), (0, 100, 100), (100, 100, 100)]:
        assert conv.hex_to_pct(conv.pct_to_hex(rgb)) == rgb


def test_kelvin_calido_tira_a_rojo():
    r, g, b = conv.kelvin_to_pct(2700)
    assert r == 100 and r > g > b


def test_kelvin_6500_casi_blanco():
    r, g, b = conv.kelvin_to_pct(6500)
    assert min(r, g, b) >= 95


def test_kelvin_frio_tira_a_azul():
    r, g, b = conv.kelvin_to_pct(12000)
    assert b == 100 and b > r


@pytest.mark.parametrize("k", [500, 50000])
def test_kelvin_fuera_de_rango(k):
    with pytest.raises(ValueError):
        conv.kelvin_to_pct(k)
