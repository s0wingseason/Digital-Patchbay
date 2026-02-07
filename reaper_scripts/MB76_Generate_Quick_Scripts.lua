--[[
  MB-76 Patchbay Controller - Quick Bank Recall Scripts
  Individual scripts for banks 1-8 (can be assigned to toolbar/hotkeys)
  
  This file generates wrapper scripts that call specific banks.
]]--

-- Quick recall functions for banks 1-8
-- Each can be saved as a separate script or used via the master script

local script_path = ({reaper.get_action_context()})[2]:match("(.*/)")
if not script_path then script_path = "" end

-- HTTP-based bank recall (connects to Python backend)
function recall_bank_http(bank)
    local url = string.format("http://127.0.0.1:5000/api/bank/%d", bank)
    local cmd = string.format('curl -s -X POST "%s" > nul 2>&1', url)
    os.execute(cmd)
    reaper.ShowConsoleMsg(string.format("MB-76: Quick Recalled Bank %d\n", bank))
end

-- Generate individual bank scripts
function generate_bank_scripts()
    for bank = 1, 32 do
        local script_content = string.format([[
--[[
  MB-76 Quick Recall - Bank %d
  Auto-generated script for toolbar/hotkey binding
]]--

local function recall_bank_http(bank)
    local url = string.format("http://127.0.0.1:5000/api/bank/%%d", bank)
    local cmd = string.format('curl -s -X POST "%%s" > nul 2>&1', url)
    os.execute(cmd)
    reaper.ShowConsoleMsg(string.format("MB-76: Recalled Bank %%d\n", bank))
end

recall_bank_http(%d)
]], bank, bank)
        
        local filename = script_path .. string.format("MB76_Bank_%02d.lua", bank)
        local file = io.open(filename, "w")
        if file then
            file:write(script_content)
            file:close()
        end
    end
    
    reaper.ShowConsoleMsg("MB-76: Generated 32 quick bank recall scripts\n")
end

-- Run generation
generate_bank_scripts()

reaper.ShowMessageBox(
    "Generated 32 quick bank recall scripts!\n\n" ..
    "You can now find MB76_Bank_01.lua through MB76_Bank_32.lua\n" ..
    "in the Scripts folder and assign them to toolbar buttons.",
    "MB-76 Script Generator",
    0
)
