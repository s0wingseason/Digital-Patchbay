# MB-76 Digital Patchbay Controller

A modern, web-based control interface for the **Akai MB-76 Digital Patchbay**, integrated with REAPER.

![MB-76 Controller](https://via.placeholder.com/800x400/1a1a25/6366f1?text=MB-76+Patchbay+Controller)

https://imgur.com/a/aNM8J0X

## Features

- 🎛️ **Visual Routing Matrix** — 7×6 grid showing all input-to-output routing
- 💾 **Preset Management** — Save and recall routing configurations
- 🎹 **MIDI Control** — Send Program Change to recall MB-76 banks (1-32)
- 🎨 **Modern Dark UI** — Flock Audio-inspired design with glassmorphism effects
- 🔧 **User-Configurable I/O** — Rename inputs/outputs to match your studio
- 🎬 **REAPER Integration** — Lua scripts for toolbar/hotkey integration

---

## Quick Start

### One-Click Installation

1. **Double-click `build_and_run.bat`** — This handles everything:
   - Checks for Python
   - Creates virtual environment
   - Installs dependencies
   - Copies REAPER scripts
   - Creates desktop shortcut
   - Launches the application

2. **Open your browser** to `http://127.0.0.1:5000`

3. **Configure your MIDI device** via the ⚙️ Settings button

### Requirements

- **Python 3.10+** — [Download here](https://www.python.org/downloads/)
  - ⚠️ Check "Add Python to PATH" during installation!
- **Windows 10/11**
- **REAPER** (optional, for script integration)

---

## Usage

### Web Interface

1. **Routing Matrix**: Click crosspoints to toggle routing (visual reference only)
2. **Quick Banks**: Click bank buttons 1-32 to instantly recall MB-76 banks
3. **Presets**: Save current routing as presets, recall them with one click
4. **Settings**: Configure MIDI device, channel, and I/O labels

### REAPER Scripts

After installation, the following scripts are available in REAPER:

| Script | Description |
|--------|-------------|
| `MB76_Recall_Bank.lua` | Dialog to enter bank number (1-32) |
| `MB76_Launch_WebUI.lua` | Open web interface in browser |
| `MB76_Generate_Quick_Scripts.lua` | Generate 32 individual bank scripts |

**To add scripts to REAPER:**
1. Open REAPER → Actions → Show action list
2. Click "Load ReaScript"
3. Navigate to `%APPDATA%\REAPER\Scripts\MB-76\`
4. Select desired scripts
5. Assign to toolbar buttons or hotkeys

---

## How It Works

The **Akai MB-76** responds to MIDI Program Change messages:
- Program Change 0-31 = Bank 1-32
- The MB-76 recalls the routing configuration stored in that bank

**Important**: You must first program your routing configurations on the MB-76 itself. This software only *recalls* those pre-programmed banks via MIDI.

```
[Web UI] → [Python Server] → [MIDI Output] → [MB-76]
              ↓
         [REAPER Lua Scripts]
```

---

## File Structure

```
Digital Patchbay/
├── app.py                 # Flask server (main application)
├── midi_controller.py     # MIDI communication
├── preset_manager.py      # Preset save/load
├── config.json            # Application settings
├── requirements.txt       # Python dependencies
│
├── static/                # Web interface
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── presets/               # Saved preset files
│
├── reaper_scripts/        # REAPER Lua scripts
│   ├── MB76_Recall_Bank.lua
│   ├── MB76_Launch_WebUI.lua
│   └── MB76_Generate_Quick_Scripts.lua
│
├── install.bat            # One-click installer
├── launch.bat             # Application launcher
├── build_and_run.bat      # Master build/install/run script
└── uninstall.bat          # Cleanup script
```

---

## Configuration

Edit `config.json` to customize:

```json
{
  "midi": {
    "channel": 1,        // MIDI channel (1-16)
    "device": null       // Auto-detected, or specify name
  },
  "mb76": {
    "inputs": [...],     // Rename inputs
    "outputs": [...]     // Rename outputs
  },
  "server": {
    "host": "127.0.0.1",
    "port": 5000
  }
}
```

---

## Troubleshooting

### "No MIDI devices found"
- Check that your MIDI interface is connected
- Ensure MIDI drivers are installed
- Try refreshing the device list in Settings

### "Connection refused"
- Make sure the Python server is running
- Check that port 5000 isn't blocked by firewall

### REAPER scripts not working
- Verify the web server is running
- Check REAPER console for error messages
- Ensure curl is available (comes with Windows 10+)

---

## License

MIT License - Feel free to modify and share!

---

## Credits

Inspired by:
- [Flock Audio PATCH](https://flockaudio.com/)
- [Tegeler Audio Konnektor](https://tegeler.com/)
- [Z-Systems Digital Detangler](https://z-sys.com/)

Built with ❤️ for studio workflow optimization.
