"""
MB-76 Digital Patchbay Controller - Main Flask Application
A web-based control interface for the Akai MB-76 Digital Patchbay.
"""

import json
import os
import webbrowser
import threading
from flask import Flask, jsonify, request, send_from_directory, render_template_string
from flask_cors import CORS

from midi_controller import get_midi_controller, MIDIController
from preset_manager import get_preset_manager, PresetManager, Preset

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Configuration
CONFIG_PATH = "config.json"


def load_config() -> dict:
    """Load application configuration."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """Save application configuration."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


# =============================================================================
# Static File Routes
# =============================================================================

@app.route('/')
def index():
    """Serve the main application page."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


# =============================================================================
# Configuration API
# =============================================================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current application configuration."""
    config = load_config()
    midi = get_midi_controller()
    
    return jsonify({
        "config": config,
        "midi_status": midi.get_status()
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update application configuration."""
    data = request.get_json()
    config = load_config()
    
    # Update MIDI settings
    if 'midi_channel' in data:
        midi = get_midi_controller()
        if midi.set_midi_channel(data['midi_channel']):
            config['midi']['channel'] = data['midi_channel']
    
    if 'midi_device' in data:
        midi = get_midi_controller()
        if midi.set_midi_device(data['midi_device']):
            config['midi']['device'] = data['midi_device']
    
    # Update I/O names
    if 'inputs' in data:
        config['mb76']['inputs'] = data['inputs']
    if 'outputs' in data:
        config['mb76']['outputs'] = data['outputs']
    
    save_config(config)
    
    return jsonify({"success": True, "config": config})


# =============================================================================
# MIDI API
# =============================================================================

@app.route('/api/midi/devices', methods=['GET'])
def get_midi_devices():
    """Get available MIDI output devices."""
    midi = get_midi_controller()
    return jsonify({
        "devices": midi.get_available_outputs(),
        "current_device": midi.midi_device,
        "current_channel": midi.midi_channel + 1
    })


@app.route('/api/midi/connect', methods=['POST'])
def connect_midi():
    """Connect to MIDI device."""
    data = request.get_json() or {}
    midi = get_midi_controller()
    
    if 'device' in data:
        midi.set_midi_device(data['device'])
    
    success = midi.connect()
    return jsonify({
        "success": success,
        "status": midi.get_status()
    })


@app.route('/api/midi/disconnect', methods=['POST'])
def disconnect_midi():
    """Disconnect from MIDI device."""
    midi = get_midi_controller()
    midi.disconnect()
    return jsonify({"success": True})


# =============================================================================
# Bank Recall API
# =============================================================================

@app.route('/api/bank/<int:bank_number>', methods=['POST'])
def recall_bank(bank_number: int):
    """Recall an MB-76 bank (1-32)."""
    if not 1 <= bank_number <= 32:
        return jsonify({"error": "Bank number must be between 1 and 32"}), 400
    
    midi = get_midi_controller()
    success = midi.recall_bank(bank_number)
    
    return jsonify({
        "success": success,
        "bank": bank_number,
        "message": f"Bank {bank_number} recalled" if success else "Failed to recall bank"
    })


@app.route('/api/bank/send-program-change', methods=['POST'])
def send_program_change():
    """Send a raw program change message."""
    data = request.get_json()
    program = data.get('program', 0)
    
    if not 0 <= program <= 127:
        return jsonify({"error": "Program must be between 0 and 127"}), 400
    
    midi = get_midi_controller()
    success = midi.send_program_change(program)
    
    return jsonify({
        "success": success,
        "program": program
    })


# =============================================================================
# Preset API
# =============================================================================

@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get all presets."""
    manager = get_preset_manager()
    return jsonify({
        "presets": manager.get_presets_summary()
    })


@app.route('/api/presets', methods=['POST'])
def create_preset():
    """Create a new preset."""
    data = request.get_json()
    
    name = data.get('name', 'New Preset')
    bank_number = data.get('bank_number', 1)
    routing_matrix = data.get('routing_matrix', {})
    description = data.get('description', '')
    
    manager = get_preset_manager()
    preset = manager.create_preset(
        name=name,
        bank_number=bank_number,
        routing_matrix=routing_matrix,
        description=description
    )
    
    if preset:
        return jsonify({
            "success": True,
            "preset": preset.to_dict()
        })
    return jsonify({"error": "Failed to create preset"}), 400


@app.route('/api/presets/<preset_id>', methods=['GET'])
def get_preset(preset_id: str):
    """Get a specific preset."""
    manager = get_preset_manager()
    preset = manager.get_preset(preset_id)
    
    if preset:
        return jsonify({"preset": preset.to_dict()})
    return jsonify({"error": "Preset not found"}), 404


@app.route('/api/presets/<preset_id>', methods=['PUT'])
def update_preset(preset_id: str):
    """Update a preset."""
    data = request.get_json()
    manager = get_preset_manager()
    
    preset = manager.update_preset(preset_id, **data)
    
    if preset:
        return jsonify({
            "success": True,
            "preset": preset.to_dict()
        })
    return jsonify({"error": "Failed to update preset"}), 400


@app.route('/api/presets/<preset_id>', methods=['DELETE'])
def delete_preset(preset_id: str):
    """Delete a preset."""
    manager = get_preset_manager()
    success = manager.delete_preset(preset_id)
    
    return jsonify({"success": success})


@app.route('/api/presets/<preset_id>/recall', methods=['POST'])
def recall_preset(preset_id: str):
    """Recall a preset (send its bank number to MB-76)."""
    manager = get_preset_manager()
    preset = manager.get_preset(preset_id)
    
    if not preset:
        return jsonify({"error": "Preset not found"}), 404
    
    midi = get_midi_controller()
    success = midi.recall_bank(preset.bank_number)
    
    return jsonify({
        "success": success,
        "preset": preset.to_dict(),
        "message": f"Recalled '{preset.name}' (Bank {preset.bank_number})" if success else "Failed to recall preset"
    })


# =============================================================================
# Utility API
# =============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get overall application status."""
    config = load_config()
    midi = get_midi_controller()
    manager = get_preset_manager()
    
    return jsonify({
        "app_name": config.get("app_name", "MB-76 Patchbay Controller"),
        "version": config.get("version", "1.0.0"),
        "midi": midi.get_status(),
        "preset_count": len(manager.presets),
        "mb76": config.get("mb76", {})
    })


@app.route('/api/test', methods=['POST'])
def test_connection():
    """Test MIDI connection by sending bank 1."""
    midi = get_midi_controller()
    
    if not midi.output_port:
        if not midi.connect():
            return jsonify({
                "success": False,
                "error": "Could not connect to MIDI device"
            })
    
    success = midi.recall_bank(1)
    return jsonify({
        "success": success,
        "message": "Sent Bank 1 test message" if success else "Failed to send test message"
    })


# =============================================================================
# Application Entry Point
# =============================================================================

def open_browser(port: int):
    """Open the web browser after a short delay."""
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://127.0.0.1:{port}')


def main():
    """Run the application."""
    config = load_config()
    host = config.get("server", {}).get("host", "127.0.0.1")
    port = config.get("server", {}).get("port", 5000)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           MB-76 Digital Patchbay Controller                  ║
║                                                              ║
║   Web Interface: http://{host}:{port}                      ║
║                                                              ║
║   Press Ctrl+C to stop the server                            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize managers
    midi = get_midi_controller()
    preset_manager = get_preset_manager()
    
    # Try to connect to MIDI device
    midi.connect()
    
    # Open browser in background
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Run Flask server
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
