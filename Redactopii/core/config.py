# =============================================================================
# FILE: Redactopii/core/config.py
# DESCRIPTION: Configuration management for redaction engine
# =============================================================================

"""
Configuration management for redaction engine
"""
import json
from pathlib import Path
from typing import Dict, Optional


class RedactionConfig:
    """Configuration handler"""
    
    DEFAULT_CONFIG = {
        "default_text_method": "mask",
        "default_image_method": "blur",
        "mask_char": "█",
        "blur_intensity": 25,
        "pixelate_block_size": 15,
        "blackbox_color": [0, 0, 0],
        "padding_pixels": 5,
        "enable_encryption": False,
        "log_level": "INFO",
        "audit_trail": True,
        "confidence_threshold": 0.7,
        "output_format": "json",
        "output_base_dir": "./outputs",
        "save_comparison": True,
        "add_watermark": True
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and Path(config_path).exists():
            self.load_from_file(config_path)
    
    def load_from_file(self, path: str):
        """Load configuration from JSON file"""
        with open(path, 'r') as f:
            user_config = json.load(f)
            self.config.update(user_config)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value"""
        self.config[key] = value
    
    def save(self, path: str):
        """Save configuration to file"""
        with open(path, 'w') as f:
            json.dump(self.config, f, indent=2)