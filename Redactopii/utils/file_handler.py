"""
Handles reading and writing of files safely
"""
import os
import json
import shutil

class FileHandler:
    """Utility for safe file operations"""

    @staticmethod
    def read_text(file_path: str) -> str:
        """Reads text content from a file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_text(file_path: str, content: str):
        """Writes text content to a file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def read_json(file_path: str) -> dict:
        """Reads a JSON file"""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json(file_path: str, data: dict):
        """Writes a dictionary to a JSON file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def copy_file(src: str, dest: str):
        """Copies file from src to dest"""
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy(src, dest)
