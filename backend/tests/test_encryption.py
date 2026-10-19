import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.encryption_service import EncryptionService, EncryptionError, DecryptionError

def test_encryption_roundtrip():
    service = EncryptionService()
    original_data = b"Hello, this is a secret LAN cloud file content to be encrypted with AES-256-GCM!"
    
    ciphertext, nonce_hex, tag_hex = service.encrypt_chunk(original_data)
    
    # Ciphertext should not match original plaintext
    assert ciphertext != original_data
    assert len(nonce_hex) == 24  # 12 bytes = 24 hex characters
    assert len(tag_hex) == 32    # 16 bytes = 32 hex characters
    
    # Decryption must recover original data byte-for-byte
    decrypted = service.decrypt_chunk(ciphertext, nonce_hex, tag_hex)
    assert decrypted == original_data

def test_unique_nonces_produce_different_ciphertexts():
    service = EncryptionService()
    data = b"Same content encrypted twice"
    
    ct1, nonce1, tag1 = service.encrypt_chunk(data)
    ct2, nonce2, tag2 = service.encrypt_chunk(data)
    
    # Nonces must be unique
    assert nonce1 != nonce2
    # Ciphertexts must differ due to unique nonces
    assert ct1 != ct2

def test_tampered_ciphertext_detection():
    service = EncryptionService()
    data = b"Sensitive college laboratory records"
    ciphertext, nonce_hex, tag_hex = service.encrypt_chunk(data)
    
    # Flip the first byte of ciphertext
    tampered_ct = bytearray(ciphertext)
    tampered_ct[0] ^= 0xFF
    
    # Decryption must fail due to AES-GCM authentication tag verification
    with pytest.raises(DecryptionError, match="authentication tag mismatch or corrupted data"):
        service.decrypt_chunk(bytes(tampered_ct), nonce_hex, tag_hex)

def test_tampered_tag_detection():
    service = EncryptionService()
    data = b"Exam questions data"
    ciphertext, nonce_hex, tag_hex = service.encrypt_chunk(data)
    
    # Corrupt tag
    tampered_tag = "0" * 32
    with pytest.raises(DecryptionError):
        service.decrypt_chunk(ciphertext, nonce_hex, tampered_tag)

def test_invalid_key_length():
    with pytest.raises(ValueError, match="32-byte"):
        EncryptionService(key=b"too_short_key")

