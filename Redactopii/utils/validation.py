"""
Validates file paths, inputs, and configuration formats
"""
import os
import json

class Validation:
    """Validation utilities"""

    @staticmethod
    def validate_file_exists(path: str):
        """Checks if the given file exists"""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")

    @staticmethod
    def validate_json_format(file_path: str):
        """Validates that a file is a proper JSON"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format: {file_path}")

    @staticmethod
    def validate_output_dir(dir_path: str):
        """Ensures the output directory exists"""
        os.makedirs(dir_path, exist_ok=True)
