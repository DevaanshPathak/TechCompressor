"""
Tests for techcompressor.crypto module (AES-256-GCM encryption)
"""

import os
import pytest
from techcompressor.crypto import (
    derive_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    MAGIC_HEADER_ENCRYPTED,
    SALT_SIZE,
    NONCE_SIZE,
)


def test_derive_key_basic():
    """Test basic key derivation."""
    password = "test_password"
    salt = os.urandom(SALT_SIZE)
    
    key = derive_key(password, salt)
    
    assert isinstance(key, bytes)
    assert len(key) == 32  # 256 bits
    
    # Same password and salt should produce same key
    key2 = derive_key(password, salt)
    assert key == key2


def test_derive_key_different_salts():
    """Test that different salts produce different keys."""
    password = "test_password"
    salt1 = os.urandom(SALT_SIZE)
    salt2 = os.urandom(SALT_SIZE)
    
    key1 = derive_key(password, salt1)
    key2 = derive_key(password, salt2)
    
    assert key1 != key2


def test_derive_key_different_passwords():
    """Test that different passwords produce different keys."""
    salt = os.urandom(SALT_SIZE)
    
    key1 = derive_key("password1", salt)
    key2 = derive_key("password2", salt)
    
    assert key1 != key2


def test_derive_key_empty_password():
    """Test that empty password raises ValueError."""
    salt = os.urandom(SALT_SIZE)
    
    with pytest.raises(ValueError, match="Password cannot be empty"):
        derive_key("", salt)


def test_derive_key_invalid_salt_size():
    """Test that invalid salt size raises ValueError."""
    password = "test_password"
    
    with pytest.raises(ValueError, match="Salt must be"):
        derive_key(password, b"short")


def test_roundtrip_encryption():
    """Test that encryption followed by decryption recovers original data."""
    plaintext = b"CONFIDENTIAL DATA 12345"
    password = "secure_password_123"
    
    # Encrypt
    encrypted = encrypt_aes_gcm(plaintext, password)
    
    # Verify it's different from plaintext
    assert encrypted != plaintext
    
    # Verify magic header
    assert encrypted[:4] == MAGIC_HEADER_ENCRYPTED
    
    # Decrypt
    decrypted = decrypt_aes_gcm(encrypted, password)
    
    # Verify original data recovered
    assert decrypted == plaintext


def test_wrong_password():
    """Test that wrong password raises ValueError."""
    plaintext = b"SECRET MESSAGE"
    password = "correct_password"
    wrong_password = "wrong_password"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decrypt_aes_gcm(encrypted, wrong_password)


def test_empty_input():
    """Test encryption and decryption of empty data."""
    plaintext = b""
    password = "password123"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    decrypted = decrypt_aes_gcm(encrypted, password)
    
    assert decrypted == plaintext


def test_random_data():
    """Test encryption of random binary data."""
    plaintext = os.urandom(1024)
    password = "random_pass"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    decrypted = decrypt_aes_gcm(encrypted, password)
    
    assert decrypted == plaintext


def test_large_data():
    """Test encryption of large data."""
    plaintext = b"X" * 100000  # 100 KB
    password = "large_data_pass"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    decrypted = decrypt_aes_gcm(encrypted, password)
    
    assert decrypted == plaintext


def test_salt_uniqueness():
    """Test that each encryption uses a unique salt."""
    plaintext = b"SAME DATA"
    password = "same_password"
    
    encrypted1 = encrypt_aes_gcm(plaintext, password)
    encrypted2 = encrypt_aes_gcm(plaintext, password)
    
    # Extract salts (after 4-byte magic header)
    salt1 = encrypted1[4:4+SALT_SIZE]
    salt2 = encrypted2[4:4+SALT_SIZE]
    
    # Salts should be different (random)
    assert salt1 != salt2
    
    # Encrypted data should be different
    assert encrypted1 != encrypted2
    
    # But both should decrypt to same plaintext
    assert decrypt_aes_gcm(encrypted1, password) == plaintext
    assert decrypt_aes_gcm(encrypted2, password) == plaintext


def test_nonce_uniqueness():
    """Test that each encryption uses a unique nonce."""
    plaintext = b"TEST DATA"
    password = "test_pass"
    
    encrypted1 = encrypt_aes_gcm(plaintext, password)
    encrypted2 = encrypt_aes_gcm(plaintext, password)
    
    # Extract nonces (after 4-byte magic + 16-byte salt)
    nonce1 = encrypted1[4+SALT_SIZE:4+SALT_SIZE+NONCE_SIZE]
    nonce2 = encrypted2[4+SALT_SIZE:4+SALT_SIZE+NONCE_SIZE]
    
    # Nonces should be different (random)
    assert nonce1 != nonce2


def test_corrupted_data():
    """Test that corrupted encrypted data raises ValueError."""
    plaintext = b"ORIGINAL DATA"
    password = "password"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    
    # Corrupt the ciphertext (flip a bit in the middle)
    corrupted = bytearray(encrypted)
    corrupted[len(corrupted) // 2] ^= 0xFF
    corrupted = bytes(corrupted)
    
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decrypt_aes_gcm(corrupted, password)


def test_truncated_data():
    """Test that truncated encrypted data raises ValueError."""
    plaintext = b"DATA"
    password = "pass"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    
    # Truncate the data
    truncated = encrypted[:20]
    
    with pytest.raises(ValueError, match="Encrypted data too short"):
        decrypt_aes_gcm(truncated, password)


def test_invalid_magic_header():
    """Test that invalid magic header raises ValueError."""
    password = "pass"
    fake_data = b"FAKE" + b"\x00" * 50
    
    with pytest.raises(ValueError, match="Invalid magic header"):
        decrypt_aes_gcm(fake_data, password)


def test_empty_password():
    """Test that empty password raises ValueError."""
    plaintext = b"DATA"
    
    with pytest.raises(ValueError, match="Password cannot be empty"):
        encrypt_aes_gcm(plaintext, "")
    
    encrypted = b"TCE1" + b"\x00" * 50
    with pytest.raises(ValueError, match="Password cannot be empty"):
        decrypt_aes_gcm(encrypted, "")


def test_unicode_password():
    """Test that unicode passwords work correctly."""
    plaintext = b"SECRET"
    password = "пароль密码🔐"  # Russian, Chinese, emoji
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    decrypted = decrypt_aes_gcm(encrypted, password)
    
    assert decrypted == plaintext


def test_authentication_tag_validation():
    """Test that GCM authentication tag is validated."""
    plaintext = b"AUTHENTICATED DATA"
    password = "password"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    
    # Modify the last byte (part of authentication tag)
    tampered = bytearray(encrypted)
    tampered[-1] ^= 0xFF
    tampered = bytes(tampered)
    
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decrypt_aes_gcm(tampered, password)


def test_encrypted_size():
    """Test that encrypted size is predictable."""
    plaintext = b"A" * 100
    password = "pass"
    
    encrypted = encrypt_aes_gcm(plaintext, password)
    
    # Size should be: 4 (magic) + 16 (salt) + 12 (nonce) + 100 (data) + 16 (tag) = 148
    expected_size = 4 + SALT_SIZE + NONCE_SIZE + len(plaintext) + 16
    assert len(encrypted) == expected_size


def test_binary_data_patterns():
    """Test various binary data patterns."""
    patterns = [
        b"\x00" * 100,  # All zeros
        b"\xFF" * 100,  # All ones
        b"\x00\xFF" * 50,  # Alternating
        bytes(range(256)),  # Sequential
    ]
    
    password = "pattern_test"
    
    for pattern in patterns:
        encrypted = encrypt_aes_gcm(pattern, password)
        decrypted = decrypt_aes_gcm(encrypted, password)
        assert decrypted == pattern
