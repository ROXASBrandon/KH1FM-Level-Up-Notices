-- Level Up Notices - 8 Seconds v1.0.0. Steam Global 1.0.0.2 / LuaBackend.
LUAGUI_NAME = "Level Up Notices - 8 Seconds"
LUAGUI_AUTH = "ROXASBrandon"
LUAGUI_DESC = "Holds native party level-up cards for eight seconds."
local tick
function _OnInit()
    tick = nil
    if GAME_ID ~= 0xAF71841E or ENGINE_TYPE ~= "BACKEND" then return end
    if ReadByte(0x4698D2) ~= 106 or ReadInt(0x3EA388) ~= 540680280
        or ReadByte(0x26E20C) ~= 9 then
        ConsolePrint("Level Up Notices: requires Steam Global 1.0.0.2; disabled.")
        return
    end
    local loader, reason = package.loadlib(SCRIPT_PATH .. "/io_packages/kh1_level_up_notices.dll",
                                          "kh1_notices_bootstrap")
    if not loader then
        ConsolePrint("Level Up Notices: helper unavailable: " .. tostring(reason))
        return
    end
    tick = loader
end
function _OnFrame()
    if tick then tick() end
end
