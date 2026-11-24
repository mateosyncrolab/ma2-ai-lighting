# MA2 AI Lighting — IA + control por voz para grandMA2

[![tests](https://github.com/mateosyncrolab/ma2-ai-lighting/actions/workflows/ci.yml/badge.svg)](https://github.com/mateosyncrolab/ma2-ai-lighting/actions/workflows/ci.yml)
![grandMA2](https://img.shields.io/badge/grandMA2-3.9.63.6-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Lua](https://img.shields.io/badge/lua-plugin-2C2D72)
![License](https://img.shields.io/badge/license-MIT-green)

**Iluminación de conciertos controlada con inteligencia artificial y voz.**

Un set de herramientas para consolas **grandMA2** que une el control de
iluminación DMX con IA: dices *"grupo dos en rojo al cincuenta"* y la consola lo
ejecuta. El reconocimiento de voz corre con un modelo de IA **offline**, sin
depender de internet, porque en un concierto no puedes confiar en la red.

Incluye además un plugin Lua que crea en segundos toda la paleta de presets de
color globales del show, y una herramienta en Python para diseñar paletas,
convertir colores y mandar comandos a la consola por telnet.

```
"grupo dos en rojo al cincuenta"  ->  Group 2 ; Preset 4.2 ; At 50
"go executor cinco"               ->  Go Executor 5
"fixture uno al diez a full"      ->  Fixture 1 Thru 10 ; At Full
```

---

## Sobre mí

Soy ingeniero de iluminación en conciertos y festivales, y combino la consola
con programación e inteligencia artificial. En cada show llega un rig nuevo,
con fixtures de distintas marcas, y la preparación se come un tiempo que en un
montaje nunca sobra. Estas herramientas nacen de ahí: automatizar con software
e IA lo repetitivo para dedicar el tiempo al diseño de luces.

He trabajado y aplicado este flujo en producciones como:

- **Maluma — Medallo en el Mapa 2.0** (Medellín)
- **J Balvin — Ciudad Primavera**
- **Festival Estéreo Picnic**
- **Festival Cordillera**

### Cómo uso la IA

- **Control por voz:** reconocimiento de voz con redes neuronales (Vosk/Kaldi)
  que corre en el PC, sin internet, y un intérprete que traduce frases en
  español a comandos de MA2.
- **Desarrollo:** uso IA como herramienta de programación para escribir,
  revisar y probar el código del plugin y de las herramientas.
- **Automatización:** la IA me ayuda a generar y validar secuencias de comandos
  de consola. Todo pasa por tests automáticos y por grandMA2 onPC antes de
  llegar a una consola en un show.

---

## Qué hay en el repo

```
plugin/      Plugin Lua para grandMA2 (ColorPresetsGlobal)
ma2tools/    Herramienta en Python: paletas, telnet, control por voz con IA
palettes/    Paletas de color en JSON
tests/       74 tests: Python, telnet simulado y el plugin Lua real
```

| Componente | Qué hace |
|---|---|
| `plugin/ColorPresetsGlobal.lua` | Crea la paleta completa de presets de color **globales** en el Color Preset Pool |
| `ma2tools voice` | **Control de luces por voz con IA**: micrófono → modelo de voz offline → comandos de MA2 |
| `ma2tools send` | Manda la paleta a la consola por **telnet** (puerto 30000) sin pasar por el Plugin Pool |
| `ma2tools apply` | Escribe una paleta JSON dentro del plugin Lua |
| `ma2tools show` | Muestra la paleta con muestras de color reales en la terminal |
| `ma2tools convert` | Convierte hex, temperatura de color (K) o DMX 0–255 al porcentaje que usa MA2 |

---

## Control de luces por voz (IA)

La cadena completa:

```
micrófono -> Vosk (IA de voz, offline) -> texto -> intérprete -> comandos MA2 -> telnet -> consola
```

Lo que entiende:

| Frase | Comando MA2 |
|---|---|
| "fixture uno al diez" | `Fixture 1 Thru 10` |
| "grupo tres" | `Group 3` |
| "en rojo", "color azul", "fern green" | `Preset 4.x` (el slot sale de la paleta) |
| "al cincuenta", "a full", "al 80 por ciento" | `At 50` / `At Full` / `At 80` |
| "apaga" | `At 0` |
| "go executor cinco" / "atrás executor cinco" / "off executor cinco" | `Go` / `GoBack` / `Off Executor 5` |
| "executor cuatro al ochenta" | `Executor 4 At 80` |
| "macro siete" | `Macro 7` |
| "limpia" | `ClearAll` |

Se pueden encadenar: *"grupo dos en azul al setenta"*.

**Seguro para un show en vivo:** el intérprete es cerrado. La IA solo
transcribe la voz; lo que llega a la consola sale de una lista fija de
comandos. Una frase que no entiende no manda nada, y nunca pasa texto libre a
la consola (un `Delete` o un `NewShow` dicho por error no se ejecuta). Hay
tests que lo comprueban.

### Uso

```bash
pip install -e ".[voice]"

# probar con texto, sin micrófono ni consola
python -m ma2tools voice palettes/default.json --text "grupo dos en rojo al cincuenta"

# micrófono + consola (onPC en el mismo PC)
python -m ma2tools voice palettes/default.json --model models/vosk-model-small-es-0.42 --host 127.0.0.1
```

El modelo de voz en español se descarga de
[alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) y se deja
en `models/`.

---

## Plugin: presets de color globales

Seleccionas el rig, ejecutas el plugin y en segundos tienes los presets
listos, con nombre, en los slots que definiste y válidos para cualquier
fixture del show.

1. Verifica que haya fixtures seleccionados (si no, avisa y no toca nada).
2. Muestra un resumen: cantidad de colores, pool, rango de slots y modo.
3. Para cada color aplica los valores RGB y lo guarda como preset **global** con su `Label`.
4. Termina con `ClearAll` para dejar el programador limpio.

Paleta por defecto (pool 4 = Color):

| Slot | Nombre | R | G | B |
|---|---|---|---|---|
| 4.1 | White | 100 | 100 | 100 |
| 4.2 | Red | 100 | 0 | 0 |
| 4.3 | Orange | 100 | 45 | 0 |
| 4.4 | Yellow | 100 | 100 | 0 |
| 4.5 | Fern Green | 40 | 100 | 20 |
| 4.6 | Green | 0 | 100 | 0 |
| 4.8 | Cyan | 0 | 100 | 100 |
| 4.10 | Blue | 0 | 0 | 100 |
| 4.11 | Violet | 50 | 0 | 100 |
| 4.12 | Magenta | 100 | 0 | 100 |

### Global vs. selective

En grandMA2 un preset puede ser **selective** (atado a los fixtures
seleccionados), **global** (atado al tipo de fixture) o **universal**. El
plugin usa `/global`: un solo preset "Red" vale para todos los modelos del rig
con mezcla RGB, sin una macro por modelo.

Escribe los atributos `ColorRGB1` (R), `ColorRGB2` (G) y `ColorRGB3` (B) de la
librería de MA2, en porcentaje 0–100. La consola los traduce a los canales DMX
reales de cada fixture según su perfil (RGB, RGBW, CMY…).

### Instalación

1. Copia `plugin/ColorPresetsGlobal.lua` y `plugin/ColorPresetsGlobal.xml` a
   `gma2/plugins/` en la USB o en el disco de la consola. En onPC (Windows):
   ```
   C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.63\plugins\
   ```
2. **Plugin Pool** → slot vacío → **Import** → `ColorPresetsGlobal`.

Los dos archivos van juntos y con el mismo nombre base. Si la consola tiene
otra versión, cambia `major_vers`, `minor_vers` y `stream_vers` en el `.xml`.

### Configuración (bloque `USER CONFIG` del `.lua`)

| Parámetro | Default | Qué hace |
|---|---|---|
| `COLORS` | 10 colores | Se genera con `ma2tools apply` o se edita a mano |
| `PRESET_POOL` | `4` | 0=All 1=Dimmer 2=Position 3=Gobo **4=Color** 5=Beam 6=Focus 7=Control 8=Shapers 9=Video |
| `START_SLOT` | `1` | `slot = START_SLOT - 1 + num`. Con `101`, White queda en `4.101` |
| `OVERWRITE` | `true` | `false` deja que la consola pregunte en cada slot ocupado |
| `DRY_RUN` | `false` | Solo imprime los comandos en el Command Line Feedback |

---

## Paletas en JSON

```json
{
  "name": "festival",
  "colors": [
    {"num": 1,  "name": "White",     "rgb": [100, 100, 100]},
    {"num": 3,  "name": "Orange",    "hex": "#FF7300"},
    {"num": 22, "name": "Tungsteno", "kelvin": 3200}
  ]
}
```

Cada color se define en porcentaje MA2, en hex o por temperatura de color.

```bash
python -m ma2tools show palettes/whites-kelvin.json        # ver la paleta
python -m ma2tools apply palettes/default.json             # escribirla en el plugin
python -m ma2tools commands palettes/default.json --with-undo
python -m ma2tools send palettes/default.json --host 192.168.0.10 --select "Group 1"
python -m ma2tools convert 5600K                           # -> "rgb": [100, 94, 88]
```

`send` y `commands` generan **exactamente** la misma secuencia que el plugin
Lua; hay un test que corre el plugin real y compara las dos.

---

## Especificaciones

### Software

| | |
|---|---|
| Consola | grandMA2 (full-size, light, ultra-light, onPC) |
| Versión probada | **grandMA2 onPC 3.9.63.6** |
| XML de import | `3.9.63/MA.xsd` (`major_vers="3" minor_vers="9" stream_vers="63"`) |
| Plugin | Lua, API `gma`: `gma.cmd`, `gma.echo`, `gma.feedback`, `gma.gui.confirm`, `gma.show.getvar` |
| Herramientas | Python 3.10+, sin dependencias obligatorias |
| IA de voz | Vosk (Kaldi), modelo en español, 100 % offline |
| Comunicación | Telnet al command line de MA2, puerto 30000 |

### Consola de referencia: grandMA2 full-size

| | |
|---|---|
| Parámetros | 8.192 HTP/LTP en consola; hasta 65.536 (256 universos DMX) con MA NPU |
| DMX | 6 salidas DMX (XLR 5 pines) + 1 entrada DMX |
| Pantallas | 3 touchscreens de 15,4" + 1 pantalla de comandos multitáctil de 9" + 2 salidas para monitores externos |
| Faders | 30 executors motorizados + 2 faders A/B motorizados de 100 mm |
| Red | MA-Net2 / Art-Net / sACN |

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

- El **plugin Lua real** se ejecuta con una API `gma` simulada (sin consola)
  para comprobar comandos, diálogos, cancelación y dry-run.
- El cliente telnet se prueba contra un servidor TCP que imita a la consola.
- El intérprete de voz se prueba con frases reales y con frases peligrosas que
  no deben llegar a la consola.

GitHub Actions corre todo en Python 3.10, 3.12 y 3.13 en cada push.

---

## Próximamente: grandMA3 + más IA

- [ ] Port del plugin a **grandMA3** (software 2.x), con su nueva API de plugins y sistema de presets.
- [ ] Control por voz para grandMA3.
- [ ] Interpretación con un modelo de lenguaje (IA generativa) para frases libres, siempre pasando por la misma lista cerrada de comandos.
- [ ] Detectar slots ocupados antes de escribir.
- [ ] Generar appearances y macros del preset.

---

Licencia MIT.
