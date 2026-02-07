--[[
  MB-76 Patchbay Controller - Launch Web Interface
  Opens the MB-76 Patchbay Controller web interface in your default browser
]]--

-- Launch the web interface
function launch_web_interface()
    local url = "http://127.0.0.1:5000"
    
    -- Windows
    if reaper.GetOS():find("Win") then
        os.execute('start "" "' .. url .. '"')
    -- macOS
    elseif reaper.GetOS():find("OSX") then
        os.execute('open "' .. url .. '"')
    -- Linux
    else
        os.execute('xdg-open "' .. url .. '"')
    end
    
    reaper.ShowConsoleMsg("MB-76: Launched web interface at " .. url .. "\n")
end

launch_web_interface()
