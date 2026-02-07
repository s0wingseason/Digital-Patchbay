"""
MB-76 Digital Patchbay - Preset Manager
Handles loading, saving, and managing routing presets.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional


class Preset:
    """Represents a routing preset configuration."""
    
    def __init__(self, 
                 name: str,
                 bank_number: int,
                 routing_matrix: Dict[str, List[int]] = None,
                 description: str = "",
                 preset_id: str = None,
                 created_at: str = None,
                 updated_at: str = None):
        self.id = preset_id or str(uuid.uuid4())
        self.name = name
        self.bank_number = bank_number  # MB-76 bank (1-32)
        self.routing_matrix = routing_matrix or {}  # {input_id: [output_ids]}
        self.description = description
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
    
    def to_dict(self) -> dict:
        """Convert preset to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "bank_number": self.bank_number,
            "routing_matrix": self.routing_matrix,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Preset':
        """Create a Preset from a dictionary."""
        return cls(
            preset_id=data.get("id"),
            name=data.get("name", "Unnamed"),
            bank_number=data.get("bank_number", 1),
            routing_matrix=data.get("routing_matrix", {}),
            description=data.get("description", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def update_routing(self, input_id: int, output_ids: List[int]) -> None:
        """Update routing for a specific input."""
        self.routing_matrix[str(input_id)] = output_ids
        self.updated_at = datetime.now().isoformat()
    
    def clear_routing(self) -> None:
        """Clear all routing assignments."""
        self.routing_matrix = {}
        self.updated_at = datetime.now().isoformat()
    
    def get_outputs_for_input(self, input_id: int) -> List[int]:
        """Get output IDs routed from a specific input."""
        return self.routing_matrix.get(str(input_id), [])


class PresetManager:
    """Manages preset storage and retrieval."""
    
    def __init__(self, presets_dir: str = "presets"):
        self.presets_dir = presets_dir
        self._ensure_directory()
        self.presets: Dict[str, Preset] = {}
        self._load_all_presets()
    
    def _ensure_directory(self) -> None:
        """Ensure the presets directory exists."""
        if not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir)
    
    def _get_preset_path(self, preset_id: str) -> str:
        """Get the file path for a preset."""
        return os.path.join(self.presets_dir, f"{preset_id}.json")
    
    def _load_all_presets(self) -> None:
        """Load all presets from the presets directory."""
        self.presets = {}
        if not os.path.exists(self.presets_dir):
            return
            
        for filename in os.listdir(self.presets_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.presets_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        preset = Preset.from_dict(data)
                        self.presets[preset.id] = preset
                except Exception as e:
                    print(f"Error loading preset {filename}: {e}")
    
    def save_preset(self, preset: Preset) -> bool:
        """Save a preset to disk."""
        try:
            filepath = self._get_preset_path(preset.id)
            with open(filepath, 'w') as f:
                json.dump(preset.to_dict(), f, indent=2)
            self.presets[preset.id] = preset
            return True
        except Exception as e:
            print(f"Error saving preset: {e}")
            return False
    
    def create_preset(self, name: str, bank_number: int, 
                     routing_matrix: Dict = None, 
                     description: str = "") -> Optional[Preset]:
        """Create and save a new preset."""
        if not 1 <= bank_number <= 32:
            print(f"Invalid bank number: {bank_number}. Must be 1-32.")
            return None
            
        preset = Preset(
            name=name,
            bank_number=bank_number,
            routing_matrix=routing_matrix or {},
            description=description
        )
        
        if self.save_preset(preset):
            return preset
        return None
    
    def get_preset(self, preset_id: str) -> Optional[Preset]:
        """Get a preset by ID."""
        return self.presets.get(preset_id)
    
    def get_preset_by_bank(self, bank_number: int) -> Optional[Preset]:
        """Get the first preset assigned to a specific bank number."""
        for preset in self.presets.values():
            if preset.bank_number == bank_number:
                return preset
        return None
    
    def get_all_presets(self) -> List[Preset]:
        """Get all presets, sorted by bank number."""
        return sorted(self.presets.values(), key=lambda p: (p.bank_number, p.name))
    
    def update_preset(self, preset_id: str, **kwargs) -> Optional[Preset]:
        """Update a preset's properties."""
        preset = self.get_preset(preset_id)
        if not preset:
            return None
        
        if 'name' in kwargs:
            preset.name = kwargs['name']
        if 'bank_number' in kwargs:
            if not 1 <= kwargs['bank_number'] <= 32:
                print(f"Invalid bank number: {kwargs['bank_number']}")
                return None
            preset.bank_number = kwargs['bank_number']
        if 'routing_matrix' in kwargs:
            preset.routing_matrix = kwargs['routing_matrix']
        if 'description' in kwargs:
            preset.description = kwargs['description']
        
        preset.updated_at = datetime.now().isoformat()
        
        if self.save_preset(preset):
            return preset
        return None
    
    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset."""
        if preset_id not in self.presets:
            return False
        
        try:
            filepath = self._get_preset_path(preset_id)
            if os.path.exists(filepath):
                os.remove(filepath)
            del self.presets[preset_id]
            return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    
    def get_presets_summary(self) -> List[Dict]:
        """Get a summary of all presets for display."""
        return [
            {
                "id": p.id,
                "name": p.name,
                "bank_number": p.bank_number,
                "description": p.description,
                "route_count": len(p.routing_matrix),
                "updated_at": p.updated_at
            }
            for p in self.get_all_presets()
        ]
    
    def create_default_presets(self) -> None:
        """Create default presets for all 32 banks if none exist."""
        if self.presets:
            return  # Don't overwrite existing presets
            
        for bank in range(1, 33):
            self.create_preset(
                name=f"Bank {bank}",
                bank_number=bank,
                description=f"Default preset for MB-76 Bank {bank}"
            )


# Singleton instance
_preset_manager: Optional[PresetManager] = None

def get_preset_manager() -> PresetManager:
    """Get or create the singleton PresetManager instance."""
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = PresetManager()
    return _preset_manager


if __name__ == "__main__":
    # Test the preset manager
    manager = PresetManager()
    
    # Create a test preset
    preset = manager.create_preset(
        name="Mixing Session",
        bank_number=1,
        routing_matrix={"1": [1, 2], "2": [3]},
        description="Standard mixing configuration"
    )
    
    if preset:
        print(f"Created preset: {preset.name} (ID: {preset.id})")
        print(f"Routing: {preset.routing_matrix}")
    
    # List all presets
    print("\nAll presets:")
    for p in manager.get_all_presets():
        print(f"  Bank {p.bank_number}: {p.name}")
