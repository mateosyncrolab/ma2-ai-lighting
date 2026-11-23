# ColorPresetsGlobal — presets de color globales para grandMA2

Plugin de grandMA2 que crea presets de color **globales** en el Color Preset Pool
a partir de una tabla de valores definida dentro del script.

Global = el preset no queda atado a un fixture type. Un solo preset "Red" sirve
para todos los modelos del rig, así que no hace falta una macro por modelo.

**Alcance de esta etapa: solo presets.** No genera macros, ni appearances, no
toca el Layout View, no lee el patch.

---

## Archivos

| Archivo | Qué es |
|---|---|
| `ColorPresetsGlobal.lua` | El plugin |
| `ColorPresetsGlobal.xml` | Wrapper de import (apunta al `.lua`) |

Los dos tienen que viajar **juntos y en la misma carpeta**, con el mismo nombre
base. Si renombrás uno tenés que renombrar el otro y además actualizar el
atributo `luafile=` dentro del `.xml`.

Versión de consola de destino: **grandMA2 3.9.63** (el XML declara
`3.9.63/MA.xsd`, `major_vers="3" minor_vers="9" stream_vers="63"`).
Si importás en una consola con otra build, cambiá esos tres valores por los que
escriba esa consola al exportar cualquier objeto (mirá el header de un XML suyo).

---

## Instalar

1. Copiá `ColorPresetsGlobal.lua` y `ColorPresetsGlobal.xml` a la carpeta
   `gma2/plugins/` de la USB o del disco de la consola.

   En onPC (Windows) esa carpeta es:
   ```
   C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.63\plugins\
   ```

2. En la consola, abrí el **Plugin Pool**.
3. Tocá un slot vacío → **Import** → elegí `ColorPresetsGlobal`.
4. El plugin queda en ese slot listo para ejecutar.

## Usar

1. **Seleccioná los fixtures** que querés usar como base del preset (puede ser
   una selección mixta de tipos: eso es justamente el punto de un preset global).
2. Ejecutá el plugin desde el Plugin Pool.
3. Aparece un diálogo con la cantidad de colores, el pool y el rango de slots.
   Confirmá o cancelá.
4. Al terminar muestra un resumen y **deja el programador limpio** (`ClearAll`).

Si corrés el plugin sin selección activa, avisa con un diálogo y sale sin tocar
nada.

---

## Editar la tabla de colores

Todo lo editable está al principio del `.lua`, en el bloque marcado
`USER CONFIG`.

```lua
local COLORS = {
  { num =  1, name = "White",      r = 100, g = 100, b = 100 },
  { num =  2, name = "Red",        r = 100, g =   0, b =   0 },
  ...
}
```

- `num` — número de color según la numeración del show. **No es el slot final**,
  ver `START_SLOT`.
- `name` — el nombre que se le pone al preset (`Label`).
- `r`, `g`, `b` — 0..100 (porcentaje, igual que el command line de MA2).

Los RGB que vienen son una **propuesta de arranque**. Ajustalos a mano después de
ver cómo responden los fixtures reales; es normal que "Orange" o "Fern Green"
necesiten retoque por rig.

Para agregar un color: agregá una línea más a la tabla. Para sacar uno: borrá o
comentá la línea con `--` al principio.

### Otros parámetros

| Parámetro | Default | Qué hace |
|---|---|---|
| `PRESET_POOL` | `4` | Pool de destino. 0=All 1=Dimmer 2=Position 3=Gobo **4=Color** 5=Beam 6=Focus 7=Control 8=Shapers 9=Video |
| `START_SLOT` | `1` | Slot del primer color. El slot de cada color es `START_SLOT - 1 + num`. Con `1`, los slots coinciden exactamente con la columna `num` (1,2,3,4,5,6,8,10,11,12). Con `101`, White va a `4.101`. |
| `OVERWRITE` | `true` | `true` sobrescribe slots ocupados sin preguntar. `false` deja que la consola abra su popup de Store en cada slot ocupado y decidís ahí (ver limitación abajo). |
| `DRY_RUN` | `false` | `true` no ejecuta nada: solo imprime los comandos en el Command Line Feedback. |

El plugin **solo escribe en el pool y el rango configurados**. No toca ningún
otro pool.

---

## Probar por telnet (puerto 30000)

El script está partido en dos funciones a propósito:

- `build_commands()` — devuelve la lista completa de comandos, en orden, **sin
  ejecutar nada**. Cada string es una línea válida del command line de MA2.
- `run_commands(cmds)` — ejecuta esa lista.

Para ver los comandos sin escribir en el show, poné `DRY_RUN = true` y ejecutá:
los comandos salen numerados en el Command Line Feedback y se pueden copiar tal
cual a una sesión telnet.

Con la tabla que viene por defecto, la secuencia por color es:

```
Attribute "ColorRGB1" At 100
Attribute "ColorRGB2" At 0
Attribute "ColorRGB3" At 0
Store Preset 4.2 /global /overwrite /noconfirm
Label Preset 4.2 "Red"
```

y al final, una sola vez:

```
ClearAll
```

Para probar un color suelto por telnet, seleccioná fixtures primero
(`Fixture 1 Thru 10`) y después pegá los 5 comandos de arriba.

### Por qué `/global`

Del manual de la consola (keyword `Store`, tabla de opciones):

| Opción | Corto | Descripción |
|---|---|---|
| `global` | `g` | Stores preset with global values |
| `selective` | `s` | Stores preset with selective values |
| `universal` | `u` | Stores preset with universal values |
| `overwrite` | `o` | Removes stored values and stores the new ones |
| `noconfirm` | `nc` | Suppress store confirmation pop-up |

`/global` es el switch que hace que el preset valga para cualquier fixture type
en vez de quedar ligado a los fixtures que estaban seleccionados al guardarlo.

---

## Desinstalar

1. **Borrar los presets creados** (si querés deshacer el resultado):
   ```
   Delete Preset 4.1 Thru 4.12
   ```
   Ajustá el rango si cambiaste `PRESET_POOL` o `START_SLOT`. Ese es exactamente
   el rango que muestra el diálogo de confirmación al ejecutar.

2. **Sacar el plugin del show**: en el Plugin Pool, `Delete` sobre el slot del
   plugin.

3. **Borrar los archivos**: eliminá `ColorPresetsGlobal.lua` y
   `ColorPresetsGlobal.xml` de `gma2/plugins/`.

Borrar el plugin **no** borra los presets que ya creó, y borrar los presets no
borra el plugin: son dos pasos independientes.

---

## Limitación conocida de esta etapa

`OVERWRITE = false` no puede abortar solo. Para saber si un slot ya está ocupado
haría falta `gma.show.getobj.handle("Preset 4.1")`, y esta etapa tiene prohibido
usar `gma.show.getobj`. Lo que hace hoy con `OVERWRITE = false` es no mandar
`/overwrite` ni `/noconfirm`: la consola abre su propio popup de Store en cada
slot ocupado y el operador decide (Overwrite / Merge / Cancel). La detección
automática queda para una etapa posterior. Está marcado como `TODO` al final del
`.lua`.

## API `gma` usada

Solo funciones que existen en la referencia de la consola:

- `gma.cmd(string)` → `string:error`
- `gma.echo(...)`
- `gma.feedback(...)`
- `gma.gui.confirm(title, message)` → `bool` (el `|` separa líneas en el mensaje)
- `gma.show.getvar("SELECTEDFIXTURESCOUNT")` → `string` (para el chequeo de selección)
