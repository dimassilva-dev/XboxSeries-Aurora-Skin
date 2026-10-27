-- Relógio da skin Xbox Series: hora grande e data, atualizadas a cada segundo.
-- A tela (skin\scene.xur + skin\skin.xur) foi adaptada do exemplo TemperatureManager
-- do repositório oficial XboxUnity/AuroraScripts.

scriptTitle = "Relógio"
scriptAuthor = "Xbox Series skin"
scriptVersion = 1
scriptDescription = "Hora e data do console em tela cheia, no estilo da skin Xbox Series."
scriptIcon = "icon.png"

require("AuroraUI")

local DIAS = { "domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado" }
local MESES = { "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro" }

local Xui = {}

-- lê o primeiro campo existente (a API não documenta os nomes exatos)
local function field(t, ...)
    if type(t) ~= "table" then return nil end
    for _, k in ipairs({ ... }) do
        if t[k] ~= nil then return tonumber(t[k]) end
    end
    return nil
end

-- dia da semana (1 = domingo) pelo algoritmo de Zeller, caso a API não informe
local function weekday(y, m, d)
    if m < 3 then m = m + 12; y = y - 1 end
    local k, j = y % 100, math.floor(y / 100)
    local h = (d + math.floor(13 * (m + 1) / 5) + k + math.floor(k / 4) + math.floor(j / 4) + 5 * j) % 7
    return ((h + 6) % 7) + 1
end

local function now()
    local t = Aurora.GetTime()
    local d = Aurora.GetDate()
    local hh = field(t, "Hour", "hour") or 0
    local mm = field(t, "Minute", "minute") or 0
    local ss = field(t, "Second", "second") or 0
    local clock = string.format("%02d:%02d:%02d", hh, mm, ss)

    local y = field(d, "Year", "year")
    local mo = field(d, "Month", "month")
    local da = field(d, "Day", "day")
    local date = ""
    if y and mo and da and MESES[mo] then
        local wd = field(d, "DayOfWeek", "dayofweek", "WeekDay")
        wd = wd and (wd % 7) + 1 or weekday(y, mo, da)
        date = string.format("%s, %d de %s de %d", DIAS[wd], da, MESES[mo], y)
    end
    return clock, date
end

local function refresh()
    local clock, date = now()
    Xui.clock:SetText(clock)
    Xui.date:SetText(date)
end

local function onInit(this, initData)
    Xui.clock = this:RegisterControl(XuiObject.Label, "cpuValueLabel")
    Xui.date = this:RegisterControl(XuiObject.Label, "cpuLabel")
    this:SetCommandEnabled(GizmoCommand.A, false)
    this:SetCommandEnabled(GizmoCommand.X, false)
    this:SetCommandEnabled(GizmoCommand.Y, false)
    refresh()
    this:SetTimer(1, 1000)
end

local function onTimer(this, timerId)
    refresh()
end

function main()
    local hGizmo = GizmoUI.CreateInstance()
    if hGizmo == nil then
        Script.ShowNotification("Não foi possível abrir o relógio.")
        return
    end
    hGizmo:RegisterCallback(XuiMessage.Init, onInit)
    hGizmo:RegisterCallback(XuiMessage.Timer, onTimer)
    hGizmo:InvokeUI(Script.GetBasePath(), "Relógio", "skin\\scene.xur", "skin\\skin.xur", nil)
end
