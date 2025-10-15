"""
Handles encryption and decryption for sensitive files
"""
from cryptography.fernet import Fernet
import os

class EncryptionManager:
    """Manages symmetric encryption using Fernet (AES-128 under the hood)"""
    
    def __init__(self, key: bytes = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)

    def encrypt_file(self, input_path: str, output_path: str):
        """Encrypts a file and saves it to output_path"""
        with open(input_path, 'rb') as f:
            data = f.read()
        encrypted = self.cipher.encrypt(data)
        with open(output_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_file(self, input_path: str, output_path: str):
        """Decrypts a file and saves it to output_path"""
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        with open(output_path, 'wb') as f:
            f.write(decrypted)

    def get_key(self) -> bytes:
        """Returns the encryption key"""
        return self.key

