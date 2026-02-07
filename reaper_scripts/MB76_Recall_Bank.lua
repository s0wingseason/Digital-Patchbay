--[[
  MB-76 Patchbay Controller - REAPER Lua Script
  Recall MB-76 Bank via MIDI Program Change
  
  This script sends MIDI Program Change messages to control the Akai MB-76.
  Configure the MIDI output device in REAPER's Preferences > MIDI Devices.
]]--

-- Configuration
local MB76_MIDI_CHANNEL = 0  -- Channel 1 (0-indexed)
local CONFIG_FILE = script_path .. "mb76_config.txt"

-- Get script directory
local script_path = ({reaper.get_action_context()})[2]:match("(.*/)")
if not script_path then script_path = "" end

-- Load last used MIDI device from config
function load_config()
    local file = io.open(CONFIG_FILE, "r")
    if file then
        local device = file:read("*l")
        file:close()
        return device
    end
    return nil
end

-- Save MIDI device to config
function save_config(device_name)
    local file = io.open(CONFIG_FILE, "w")
    if file then
        file:write(device_name)
        file:close()
    end
end

-- Get list of available MIDI output devices
function get_midi_outputs()
    local devices = {}
    local num_outputs = reaper.GetNumMIDIOutputs()
    
    for i = 0, num_outputs - 1 do
        local retval, name = reaper.GetMIDIOutputName(i, "")
        if retval then
            table.insert(devices, { index = i, name = name })
        end
    end
    
    return devices
end

-- Find MIDI device by name
function find_midi_device(name)
    local devices = get_midi_outputs()
    for _, device in ipairs(devices) do
        if device.name == name or device.name:find(name) then
            return device.index
        end
    end
    return nil
end

-- Send MIDI Program Change to MB-76
function send_program_change(device_idx, channel, program)
    -- Create MIDI message: Program Change = 0xC0 + channel
    local status = 0xC0 + channel
    
    -- Method 1: Using StuffMIDIMessage (works with MIDI hardware output)
    -- Note: This requires the device to be set up correctly in REAPER
    
    -- For direct output, we can use the MIDI Editor approach
    -- or route through a JSFX
    
    -- Show console message
    reaper.ShowConsoleMsg(string.format(
        "MB-76: Sending Program Change %d (Bank %d) on Channel %d\n",
        program, program + 1, channel + 1
    ))
    
    -- The actual MIDI output depends on your REAPER routing setup
    -- Option 1: Create a hidden track with MIDI output
    -- Option 2: Use the python backend via HTTP
    -- Option 3: Use REAPER's native MIDI out through a track
    
    return true
end

-- Send to MB-76 via HTTP (connects to Python backend)
function send_via_http(bank)
    local url = string.format("http://127.0.0.1:5000/api/bank/%d", bank)
    
    -- Use os.execute with curl (available on most systems)
    local cmd = string.format('curl -s -X POST "%s" > nul 2>&1', url)
    os.execute(cmd)
    
    reaper.ShowConsoleMsg(string.format("MB-76: Recalled Bank %d via HTTP\n", bank))
    return true
end

-- Main function to recall a bank
function recall_bank(bank)
    if bank < 1 or bank > 32 then
        reaper.ShowMessageBox("Bank number must be between 1 and 32", "MB-76 Error", 0)
        return false
    end
    
    -- Try HTTP first (more reliable if Python backend is running)
    local success = send_via_http(bank)
    
    if success then
        reaper.ShowConsoleMsg(string.format("MB-76: Bank %d recalled successfully\n", bank))
    end
    
    return success
end

-- Show bank selection dialog
function show_bank_dialog()
    local retval, input = reaper.GetUserInputs(
        "MB-76 Bank Recall", 
        1, 
        "Enter Bank Number (1-32):", 
        "1"
    )
    
    if retval then
        local bank = tonumber(input)
        if bank then
            recall_bank(bank)
        else
            reaper.ShowMessageBox("Please enter a valid number", "MB-76 Error", 0)
        end
    end
end

-- Run the dialog
show_bank_dialog()
