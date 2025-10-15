"""
Manages secure storage and retrieval of encryption keys
"""
import os
from cryptography.fernet import Fernet

class KeyStorage:
    """Stores and retrieves encryption keys securely"""
    
    def __init__(self, key_file: str = "security_key.key"):
        self.key_file = key_file

    def save_key(self, key: bytes):
        """Saves the encryption key securely to disk"""
        with open(self.key_file, "wb") as f:
            f.write(key)

    def load_key(self) -> bytes:
        """Loads the encryption key from disk"""
        if not os.path.exists(self.key_file):
            raise FileNotFoundError("Encryption key not found. Please generate one.")
        with open(self.key_file, "rb") as f:
            return f.read()

    def generate_and_save(self) -> bytes:
        """Generates a new key and saves it"""
        key = Fernet.generate_key()
        self.save_key(key)
        return key
