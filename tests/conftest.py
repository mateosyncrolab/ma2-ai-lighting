from pathlib import Path

import pytest

from ma2tools.palette import load

RAIZ = Path(__file__).resolve().parent.parent
PLUGIN = RAIZ / "plugin" / "ColorPresetsGlobal.lua"


@pytest.fixture
def default_palette():
    return load(RAIZ / "palettes" / "default.json")
