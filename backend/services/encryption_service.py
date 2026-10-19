import os
import logging
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from config import Config

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Base exception for encryption/decryption failures."""
    pass

class DecryptionError(EncryptionError):
    """Raised when chunk authentication tag fails or data is corrupted."""
    pass

class EncryptionService:
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize EncryptionService with a 256-bit (32-byte) key.
        Defaults to Config.get_aes_key_bytes().
        """
        self.key = key or Config.get_aes_key_bytes()
        if len(self.key) != 32:
            raise ValueError(f"AES-256 requires a 32-byte (256-bit) key, got {len(self.key)} bytes")
        self._aesgcm = AESGCM(self.key)

    def encrypt_chunk(self, data: bytes, associated_data: Optional[bytes] = None) -> Tuple[bytes, str, str]:
        """
        Encrypt a chunk of arbitrary bytes using AES-256-GCM.
        Generates a unique 96-bit (12-byte) cryptographically secure random nonce.
        
        Returns:
            Tuple of:
            - ciphertext (bytes): Raw encrypted bytes without the tag
            - nonce_hex (str): 24-character hex string (12 bytes)
            - tag_hex (str): 32-character hex string (16 bytes authentication tag)
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f"Data to encrypt must be bytes, got {type(data)}")

        nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
        try:
            # AESGCM encrypt appends 16-byte authentication tag to ciphertext
            ct_with_tag = self._aesgcm.encrypt(nonce, bytes(data), associated_data)
            ciphertext = ct_with_tag[:-16]
            tag = ct_with_tag[-16:]
            return ciphertext, nonce.hex(), tag.hex()
        except Exception as e:
            logger.error(f"Error encrypting chunk: {e}")
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt_chunk(self, ciphertext: bytes, nonce_hex: str, tag_hex: str, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt and authenticate an encrypted chunk.
        
        Args:
            ciphertext (bytes): The raw encrypted chunk bytes
            nonce_hex (str): Hex-encoded 12-byte nonce
            tag_hex (str): Hex-encoded 16-byte authentication tag
            associated_data (bytes, optional): Associated authenticated data
            
        Returns:
            bytes: The decrypted plaintext bytes
            
        Raises:
            DecryptionError: If the tag does not match (tampering/corruption) or nonce is invalid.
        """
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError(f"Ciphertext must be bytes, got {type(ciphertext)}")

        try:
            nonce = bytes.fromhex(nonce_hex)
            tag = bytes.fromhex(tag_hex)
        except (ValueError, TypeError) as e:
            raise DecryptionError(f"Invalid hex string for nonce or tag: {e}")

        if len(nonce) != 12:
            raise DecryptionError(f"Nonce must be 12 bytes (24 hex chars), got {len(nonce)} bytes")
        if len(tag) != 16:
            raise DecryptionError(f"Tag must be 16 bytes (32 hex chars), got {len(tag)} bytes")

        ct_with_tag = bytes(ciphertext) + tag
        try:
            plaintext = self._aesgcm.decrypt(nonce, ct_with_tag, associated_data)
            return plaintext
        except InvalidTag:
            logger.error("Authentication tag verification failed for chunk (corrupted or tampered data)")
            raise DecryptionError("Chunk decryption failed: authentication tag mismatch or corrupted data")
        except Exception as e:
            logger.error(f"Unexpected error during chunk decryption: {e}")
            raise DecryptionError(f"Chunk decryption failed: {e}")

