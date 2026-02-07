"""
MB-76 Digital Patchbay - MIDI Controller
Handles MIDI communication with the Akai MB-76 via Program Change messages.
"""

import json
import os
from typing import Optional, List, Dict

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    print("Warning: mido not installed. MIDI functionality will be limited.")


class MIDIController:
    """Controls MIDI output to the Akai MB-76 Digital Patchbay."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.midi_channel = self.config.get("midi", {}).get("channel", 1) - 1  # MIDI channels are 0-indexed
        self.midi_device = self.config.get("midi", {}).get("device")
        self.output_port: Optional[mido.ports.BaseOutput] = None
        
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_config(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    @staticmethod
    def get_available_outputs() -> List[str]:
        """Get list of available MIDI output devices."""
        if not MIDO_AVAILABLE:
            return []
        try:
            return mido.get_output_names()
        except Exception as e:
            print(f"Error getting MIDI outputs: {e}")
            return []
    
    def set_midi_device(self, device_name: str) -> bool:
        """Set the MIDI output device."""
        if device_name in self.get_available_outputs():
            self.midi_device = device_name
            self.config["midi"]["device"] = device_name
            self._save_config()
            # Reconnect if already connected
            if self.output_port:
                self.disconnect()
                return self.connect()
            return True
        return False
    
    def set_midi_channel(self, channel: int) -> bool:
        """Set the MIDI channel (1-16)."""
        if 1 <= channel <= 16:
            self.midi_channel = channel - 1  # Convert to 0-indexed
            self.config["midi"]["channel"] = channel
            self._save_config()
            return True
        return False
    
    def connect(self) -> bool:
        """Connect to the configured MIDI output device."""
        if not MIDO_AVAILABLE:
            print("MIDI library not available")
            return False
            
        if not self.midi_device:
            # Try to auto-select first available device
            outputs = self.get_available_outputs()
            if outputs:
                self.midi_device = outputs[0]
                print(f"Auto-selected MIDI device: {self.midi_device}")
            else:
                print("No MIDI outputs available")
                return False
        
        try:
            self.output_port = mido.open_output(self.midi_device)
            print(f"Connected to MIDI device: {self.midi_device}")
            return True
        except Exception as e:
            print(f"Error connecting to MIDI device: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MIDI output device."""
        if self.output_port:
            try:
                self.output_port.close()
            except:
                pass
            self.output_port = None
            print("Disconnected from MIDI device")
    
    def send_program_change(self, program: int) -> bool:
        """
        Send a MIDI Program Change message.
        
        Args:
            program: Program number (0-127, but MB-76 uses 0-31 for banks 1-32)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not MIDO_AVAILABLE:
            print(f"[MOCK] Would send Program Change {program} on channel {self.midi_channel + 1}")
            return True
            
        if not self.output_port:
            if not self.connect():
                return False
        
        try:
            msg = mido.Message('program_change', channel=self.midi_channel, program=program)
            self.output_port.send(msg)
            print(f"Sent Program Change {program} on channel {self.midi_channel + 1}")
            return True
        except Exception as e:
            print(f"Error sending Program Change: {e}")
            return False
    
    def recall_bank(self, bank_number: int) -> bool:
        """
        Recall an MB-76 bank (1-32).
        
        Args:
            bank_number: Bank number (1-32)
            
        Returns:
            True if bank recalled successfully, False otherwise
        """
        if not 1 <= bank_number <= 32:
            print(f"Invalid bank number: {bank_number}. Must be 1-32.")
            return False
        
        # MB-76 banks 1-32 map to Program Change 0-31
        program = bank_number - 1
        return self.send_program_change(program)
    
    def get_status(self) -> Dict:
        """Get current MIDI controller status."""
        return {
            "connected": self.output_port is not None,
            "device": self.midi_device,
            "channel": self.midi_channel + 1,  # Convert back to 1-indexed for display
            "available_devices": self.get_available_outputs(),
            "mido_available": MIDO_AVAILABLE
        }


# Singleton instance for use across the application
_midi_controller: Optional[MIDIController] = None

def get_midi_controller() -> MIDIController:
    """Get or create the singleton MIDI controller instance."""
    global _midi_controller
    if _midi_controller is None:
        _midi_controller = MIDIController()
    return _midi_controller


if __name__ == "__main__":
    # Test the MIDI controller
    controller = MIDIController()
    print("Available MIDI outputs:", controller.get_available_outputs())
    print("Status:", controller.get_status())
    
    # Test bank recall (will only work if MIDI device is connected)
    # controller.recall_bank(1)
