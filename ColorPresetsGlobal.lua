-- ColorPresetsGlobal.lua
-- grandMA2 plugin: presets de color globales
--
-- Crea presets de color en el Color Preset Pool a partir de la tabla COLORS.
-- Los presets se guardan con la opcion /global, asi que un mismo preset sirve
-- para cualquier tipo de fixture (no queda atado al fixture type).
--
-- Solo crea presets: no genera macros ni appearances, no toca el Layout View
-- y no lee el patch.
--
-- API gma usada:
--   gma.cmd(string) -> string:error
--   gma.echo(...)
--   gma.feedback(...)
--   gma.gui.confirm(string:title, string:message) -> bool
--   gma.show.getvar(string:varname) -> string
--
-- Probado contra: grandMA2 onPC 3.9.63.6


-- USER CONFIG  <<<<<  EDITAR SOLO ESTA SECCION

-- Tabla de colores.
--   num   = numero de color segun la numeracion del show (NO es el slot final,
--           ver START_SLOT mas abajo)
--   name  = nombre que se le pone al preset
--   r/g/b = valores 0..100 (porcentaje, igual que el command line de MA2)
--
-- Estos RGB son una PROPUESTA DE ARRANQUE. Ajustarlos despues de ver
-- como responden los fixtures reales.
local COLORS = {
  { num =  1, name = "White",      r = 100, g = 100, b = 100 },
  { num =  2, name = "Red",        r = 100, g =   0, b =   0 },
  { num =  3, name = "Orange",     r = 100, g =  45, b =   0 },
  { num =  4, name = "Yellow",     r = 100, g = 100, b =   0 },
  { num =  5, name = "Fern Green", r =  40, g = 100, b =  20 },
  { num =  6, name = "Green",      r =   0, g = 100, b =   0 },
  { num =  8, name = "Cyan",       r =   0, g = 100, b = 100 },
  { num = 10, name = "Blue",       r =   0, g =   0, b = 100 },
  { num = 11, name = "Violet",     r =  50, g =   0, b = 100 },
  { num = 12, name = "Magenta",    r = 100, g =   0, b = 100 },
}

-- Pool de presets de destino.
-- 0=All 1=Dimmer 2=Position 3=Gobo 4=Color 5=Beam 6=Focus 7=Control 8=Shapers 9=Video
local PRESET_POOL = 4

-- Primer slot a escribir. El slot de cada color se calcula como:
--     slot = START_SLOT - 1 + color.num
-- Con START_SLOT = 1 los slots coinciden exactamente con la columna "num"
-- de la tabla (1,2,3,4,5,6,8,10,11,12). Subirlo para desplazar todo el bloque
-- (p. ej. START_SLOT = 101 -> White va a 4.101).
local START_SLOT = 1

-- true  -> sobrescribe slots ocupados sin preguntar (Store ... /overwrite /noconfirm)
-- false -> no sobrescribe en silencio: si el slot esta ocupado la consola abre
--          su popup de Store y el operador decide (Overwrite / Merge / Cancel).
--          Ver la nota TODO al final del archivo.
local OVERWRITE = true

-- true  -> no ejecuta nada, solo imprime los comandos en el Command Line
--          Feedback. Util para copiarlos y probarlos sueltos por telnet:30000.
local DRY_RUN = false

-- FIN USER CONFIG


local PLUGIN_NAME = "ColorPresetsGlobal"

-- Nombre de los tres atributos RGB en la libreria de MA2.
local ATTR_R = "ColorRGB1"
local ATTR_G = "ColorRGB2"
local ATTR_B = "ColorRGB3"


-- slot_of(color) -> numero de slot dentro del pool
local function slot_of(color)
  return START_SLOT - 1 + color.num
end


-- slot_range() -> primer slot, ultimo slot
local function slot_range()
  local lo, hi
  for _, color in ipairs(COLORS) do
    local s = slot_of(color)
    if (lo == nil) or (s < lo) then lo = s end
    if (hi == nil) or (s > hi) then hi = s end
  end
  return lo, hi
end


-- store_options() -> string con las opciones del comando Store
--
-- /global (/g)    : fuerza preset GLOBAL. Este es el switch que hace que el
--                   preset no quede atado a un fixture type.
-- /overwrite (/o) : borra el contenido previo del slot y escribe el nuevo.
-- /noconfirm (/nc): no abre el popup de confirmacion.
local function store_options()
  if OVERWRITE then
    return " /global /overwrite /noconfirm"
  end
  return " /global"
end


-- build_commands() -> table de strings
--
-- Devuelve la lista COMPLETA de comandos de consola, en orden, sin ejecutar
-- nada. Cada string es una linea valida del command line de MA2, o sea que se
-- puede copiar tal cual a una sesion telnet en el puerto 30000.
local function build_commands()
  local cmds = {}
  local function add(c) cmds[#cmds + 1] = c end

  for _, color in ipairs(COLORS) do
    local target = "Preset " .. PRESET_POOL .. "." .. slot_of(color)

    add('Attribute "' .. ATTR_R .. '" At ' .. color.r)
    add('Attribute "' .. ATTR_G .. '" At ' .. color.g)
    add('Attribute "' .. ATTR_B .. '" At ' .. color.b)
    add('Store ' .. target .. store_options())
    add('Label ' .. target .. ' "' .. color.name .. '"')
  end

  -- Deja el programador limpio (valores + seleccion).
  add('ClearAll')

  return cmds
end


-- run_commands(cmds) -> ok_count, err_count
--
-- Ejecuta la lista devuelta por build_commands(). Esta separada a proposito
-- para poder generar los comandos sin ejecutarlos.
local function run_commands(cmds)
  local ok_count, err_count = 0, 0

  for i, c in ipairs(cmds) do
    if DRY_RUN then
      gma.feedback(PLUGIN_NAME .. " [dry-run " .. i .. "] " .. c)
      ok_count = ok_count + 1
    else
      local err = gma.cmd(c)
      if err then
        err_count = err_count + 1
        gma.echo(PLUGIN_NAME .. " ERROR en: " .. c .. " -> " .. tostring(err))
      else
        ok_count = ok_count + 1
      end
    end
  end

  return ok_count, err_count
end


-- selected_fixtures() -> cantidad de fixtures seleccionados
--
-- SELECTEDFIXTURESCOUNT es una variable de show de la consola; getvar devuelve
-- string, de ahi el tonumber.
local function selected_fixtures()
  return tonumber(gma.show.getvar("SELECTEDFIXTURESCOUNT")) or 0
end


-- main
local function main()
  -- 1. Verificar seleccion.
  local sel = selected_fixtures()
  if sel < 1 then
    gma.gui.confirm(PLUGIN_NAME,
      "No hay fixtures seleccionados.|" ..
      "Selecciona los fixtures y vuelve a correr el plugin.")
    gma.echo(PLUGIN_NAME .. ": abortado, no hay seleccion activa.")
    return
  end

  local lo, hi = slot_range()
  local mode
  if OVERWRITE then
    mode = "global, sobrescribe slots ocupados"
  else
    mode = "global, pregunta antes de sobrescribir"
  end

  local dry = ""
  if DRY_RUN then
    dry = "*** DRY RUN: no se escribe nada ***|"
  end

  -- 2. Confirmacion.
  local msg =
    "Fixtures seleccionados: " .. sel .. "|" ..
    "Colores a crear: " .. #COLORS .. "|" ..
    "Pool: Preset " .. PRESET_POOL .. " (Color)|" ..
    "Slots: " .. PRESET_POOL .. "." .. lo .. " thru " .. PRESET_POOL .. "." .. hi .. "|" ..
    "Modo: " .. mode .. "|" ..
    dry ..
    "Continuar?"

  if not gma.gui.confirm(PLUGIN_NAME, msg) then
    gma.echo(PLUGIN_NAME .. ": cancelado por el usuario.")
    return
  end

  -- 3 + 4. Ejecutar (build_commands ya incluye el ClearAll final).
  local cmds = build_commands()
  local ok_count, err_count = run_commands(cmds)

  -- 5. Resumen.
  local range = PRESET_POOL .. "." .. lo .. " thru " .. PRESET_POOL .. "." .. hi
  local summary =
    PLUGIN_NAME .. ": " .. #COLORS .. " presets globales en " .. range ..
    " (" .. ok_count .. " comandos ok, " .. err_count .. " con error)"
  if DRY_RUN then
    summary = summary .. " [DRY RUN]"
  end

  gma.echo(summary)
  gma.feedback(summary)
  gma.gui.confirm(PLUGIN_NAME,
    #COLORS .. " presets globales creados|" ..
    "Rango: Preset " .. range .. "|" ..
    "Comandos ok: " .. ok_count .. " / errores: " .. err_count)
end


-- TODO
--
-- OVERWRITE = false no aborta por si solo: para saber si un slot ya esta
-- ocupado habria que usar gma.show.getobj.handle("Preset 4.1"), que todavia no
-- esta implementado. Por ahora no manda /noconfirm ni /overwrite, asi que la
-- consola abre su propio popup de Store en cada slot ocupado y el operador
-- decide (Overwrite / Merge / Cancel).

return main
