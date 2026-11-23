# grandMA2 Global Color Presets

Plugin en Lua para consolas **grandMA2** que crea de un solo golpe una paleta
completa de presets de color **globales** en el Color Preset Pool.

## Por qué lo hice

Trabajo como ingeniero de iluminación en conciertos y festivales. En cada show
se repite lo mismo: llega un rig nuevo, con mezcla de fixtures de distintas
marcas, y antes de empezar a programar hay que armar la paleta de colores base.
Hacerlo a mano, color por color y tipo de fixture por tipo de fixture, se come
un tiempo que en un montaje nunca sobra.

Este plugin resuelve esa parte: seleccionas el rig, lo ejecutas y en segundos
tienes los presets listos, con nombre, en los slots que definiste y válidos
para cualquier fixture del show.

Lo he puesto en práctica en producción real, en shows como:

- **Maluma — Medallo en el Mapa 2.0** (Medellín)
- **J Balvin — Ciudad Primavera**
- **Festival Cordillera**

Detrás de esto está la forma en la que me gusta trabajar: iluminación y DMX
combinados con programación e inteligencia artificial. Uso IA como herramienta
de desarrollo para escribir y revisar código y para automatizar tareas
repetitivas de la consola, pero todo se prueba primero en grandMA2 onPC y
después en consola antes de llegar a un show.

---

## Qué hace

1. Verifica que haya fixtures seleccionados (si no, avisa y no toca nada).
2. Muestra un resumen: cantidad de colores, pool, rango de slots y modo.
3. Para cada color de la tabla, aplica los valores RGB al programador y lo
   guarda como preset **global** con su nombre (`Label`).
4. Termina con `ClearAll` para dejar el programador limpio.

Paleta incluida por defecto (pool 4 = Color):

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

Los valores van en porcentaje (0–100), igual que en el command line de MA2. Son
un punto de partida: cada rig responde distinto, sobre todo en ámbar/naranja y
verdes, y lo normal es ajustarlos en sitio.

### Global vs. selective

En grandMA2 un preset puede guardarse como **selective** (atado a los fixtures
que estaban seleccionados), **global** (atado al tipo de fixture) o
**universal**. El plugin usa `/global`, así que un solo preset "Red" funciona
para todos los modelos del rig que tengan los atributos de color RGB, sin
necesidad de una macro por modelo.

Los atributos que escribe son los de mezcla RGB de la librería de MA2:
`ColorRGB1` (R), `ColorRGB2` (G) y `ColorRGB3` (B). La consola se encarga de
traducir esos valores a los canales DMX reales de cada fixture según su perfil
(RGB, RGBW, CMY, etc.).

---

## Especificaciones

### Software

| | |
|---|---|
| Plataforma | grandMA2 (consola y grandMA2 onPC) |
| Versión probada | **grandMA2 onPC 3.9.63.6** |
| Esquema del XML de import | `3.9.63/MA.xsd` (`major_vers="3" minor_vers="9" stream_vers="63"`) |
| Lenguaje | Lua (motor de plugins de grandMA2) |
| API `gma` usada | `gma.cmd`, `gma.echo`, `gma.feedback`, `gma.gui.confirm`, `gma.show.getvar` |

### Consola de referencia: grandMA2 full-size

| | |
|---|---|
| Parámetros | 8.192 HTP/LTP en consola; hasta 65.536 (256 universos DMX) con MA NPU |
| DMX | 6 salidas DMX (XLR 5 pines) + 1 entrada DMX |
| Pantallas | 3 touchscreens internas de 15,4" + 1 pantalla de comandos multitáctil de 9" + 2 salidas para monitores externos |
| Faders | 30 executors motorizados + 2 faders A/B motorizados de 100 mm |
| Red | MA-Net2 / Art-Net / sACN para distribuir DMX por Ethernet |

El plugin no depende del modelo de consola: corre igual en full-size, light,
ultra-light y onPC con la misma versión de software.

---

## Instalación

Archivos:

| Archivo | Qué es |
|---|---|
| `ColorPresetsGlobal.lua` | El plugin |
| `ColorPresetsGlobal.xml` | Archivo de import que apunta al `.lua` |

Los dos van juntos, en la misma carpeta y con el mismo nombre base. Si
renombras uno, renombra el otro y actualiza `luafile=` dentro del `.xml`.

1. Copia los dos archivos a `gma2/plugins/` en la USB o en el disco de la
   consola. En onPC (Windows):
   ```
   C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.63\plugins\
   ```
2. Abre el **Plugin Pool**.
3. Slot vacío → **Import** → `ColorPresetsGlobal`.

Si la consola tiene otra versión de software, cambia en el `.xml` los valores
`major_vers`, `minor_vers` y `stream_vers` por los de esa consola (los puedes
ver en la cabecera de cualquier XML que exporte).

## Uso

1. Selecciona los fixtures que quieres usar como base (puede ser una selección
   mixta de tipos; para eso es el preset global).
2. Ejecuta el plugin desde el Plugin Pool.
3. Confirma en el diálogo.
4. Al terminar muestra un resumen con los comandos ejecutados y los errores, si
   hubo alguno.

## Configuración

Todo lo editable está al principio del `.lua`, en el bloque `USER CONFIG`.

| Parámetro | Default | Qué hace |
|---|---|---|
| `COLORS` | 10 colores | Tabla `num`, `name`, `r`, `g`, `b`. Agrega o comenta líneas para cambiar la paleta. |
| `PRESET_POOL` | `4` | Pool de destino. 0=All 1=Dimmer 2=Position 3=Gobo **4=Color** 5=Beam 6=Focus 7=Control 8=Shapers 9=Video |
| `START_SLOT` | `1` | Slot del primer color: `slot = START_SLOT - 1 + num`. Con `101`, White queda en `4.101`. |
| `OVERWRITE` | `true` | `true` sobrescribe sin preguntar. `false` deja que la consola abra su popup de Store en cada slot ocupado. |
| `DRY_RUN` | `false` | `true` no ejecuta nada, solo imprime los comandos en el Command Line Feedback. |

El plugin solo escribe en el pool y el rango configurados.

---

## Probar por telnet (puerto 30000)

El código separa la generación de comandos (`build_commands()`) de la ejecución
(`run_commands()`). Con `DRY_RUN = true` los comandos salen numerados en el
feedback y se pueden pegar tal cual en una sesión telnet a la consola.

Secuencia por color:

```
Attribute "ColorRGB1" At 100
Attribute "ColorRGB2" At 0
Attribute "ColorRGB3" At 0
Store Preset 4.2 /global /overwrite /noconfirm
Label Preset 4.2 "Red"
```

y al final `ClearAll`.

## Deshacer

```
Delete Preset 4.1 Thru 4.12
```

(ajusta el rango si cambiaste `PRESET_POOL` o `START_SLOT`). Borrar el plugin
del Plugin Pool no borra los presets que creó, y viceversa.

---

## Próximamente: grandMA3

La siguiente versión será para **grandMA3** (software 2.x). MA3 cambia bastante
la forma de trabajar —nueva API de plugins, nuevo sistema de presets y
recipes, fixtures con color por gel/espectro— así que no es una traducción
directa sino un port pensado para MA3.

Pendientes:

- [ ] Port a la API de plugins de grandMA3.
- [ ] Detectar slots ocupados antes de escribir, en vez de depender del popup
      de Store cuando `OVERWRITE = false`.
- [ ] Generar también appearances (color del botón del preset) y macros.
- [ ] Leer la paleta desde un archivo externo para no tener que editar el
      `.lua` en cada show.
