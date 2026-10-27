-- Require additional lua scripts
require("Enums")

-- Set some global settings that we can access later
ScriptVersion = 1.0

-- Skin Xbox Series: relógio da tela inicial.
-- Grava a hora de início do Aurora no campo light.attenuation dos layouts "Xbox Series" (no "Fundo do Jogo", hora + 30);
-- o shader das capas soma o tempo desde a abertura e desenha a hora (24 h).
-- Tudo dentro de pcall: se algo falhar, só fica registrado no log.
scriptPermissions = { "FileSystem" }

local function XboxSeriesClockStamp()
    local t = Aurora.GetTime()
    local h, m, sec = tonumber(t.Hour) or 0, tonumber(t.Minute) or 0, tonumber(t.Second) or 0
    local result = {}
    -- no "Fundo do Jogo" a hora vai com +30: o shader desenha so o relogio, sem o fundo desfocado
    for name, offset in pairs({ ["Xbox Series"] = 0, ["Xbox Series - Fundo do Jogo"] = 30 }) do
        local stamp = string.format("[ %d.0, %d.0, %d.0 ]", h + offset, m, sec)
        local path = "game:\\Media\\Layouts\\" .. name .. ".cfljson"
        local status = "nao encontrado"
        if FileSystem.FileExists(path) then
            local txt = FileSystem.ReadFile(path)
            if txt ~= nil and #txt > 0 then
                local out, n = string.gsub(txt, '"attenuation"%s*:%s*%[[^%]]*%]', '"attenuation": ' .. stamp)
                status = (n > 0 and FileSystem.WriteFile(path, out)) and ("ok " .. stamp) or ("falhou (trocas: " .. n .. ")")
            end
        end
        table.insert(result, name .. ": " .. status)
    end
    return table.concat(result, "; ")
end

local ok, msg = pcall(XboxSeriesClockStamp)
print("XboxSeries relogio: " .. (ok and tostring(msg) or ("erro: " .. tostring(msg))))

-- Let us know we are all done (Not needed..)
print(_VERSION)
print("Main.lua done!")
