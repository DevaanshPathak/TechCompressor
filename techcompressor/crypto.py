"""
TechCompressor Cryptography Module

Provides AES-256-GCM authenticated encryption for password-protected compression.
(Phase 6 implementation)
"""

import os
import struct
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .utils import get_logger

logger = get_logger(__name__)

# Magic header for encrypted data
MAGIC_HEADER_ENCRYPTED = b"TCE1"  # TechCompressor Encrypted v1

# Cryptographic parameters
PBKDF2_ITERATIONS = 100_000
KEY_SIZE = 32  # 256 bits for AES-256
SALT_SIZE = 16  # 128 bits
NONCE_SIZE = 12  # 96 bits (recommended for GCM)
TAG_SIZE = 16  # 128 bits (GCM authentication tag)


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a cryptographic key from a password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: User-provided password string
        salt: Random salt bytes (should be 16 bytes)
    
    Returns:
        32-byte derived key suitable for AES-256
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    if len(salt) != SALT_SIZE:
        raise ValueError(f"Salt must be {SALT_SIZE} bytes")
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    
    key = kdf.derive(password.encode('utf-8'))
    return key


def encrypt_aes_gcm(data: bytes, password: str) -> bytes:
    """
    Encrypt data using AES-256-GCM with password-derived key.
    
    Algorithm:
    1. Generate random salt and nonce
    2. Derive key from password using PBKDF2
    3. Encrypt data using AES-256-GCM
    4. Return formatted blob: magic + salt + nonce + ciphertext + tag
    
    Args:
        data: Plaintext bytes to encrypt
        password: Password for encryption
    
    Returns:
        Encrypted blob with header, salt, nonce, ciphertext, and authentication tag
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    logger.info(f"Encrypting {len(data)} bytes with AES-256-GCM")
    
    # Generate random salt and nonce
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    
    # Derive key
    key = derive_key(password, salt)
    
    # Encrypt with AES-256-GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)  # ciphertext includes tag
    
    # Format: magic (4) + salt (16) + nonce (12) + ciphertext + tag (included in ciphertext)
    result = MAGIC_HEADER_ENCRYPTED + salt + nonce + ciphertext
    
    logger.info(f"Encryption complete: {len(data)} → {len(result)} bytes")
    
    return result


def decrypt_aes_gcm(blob: bytes, password: str) -> bytes:
    """
    Decrypt AES-256-GCM encrypted data using password.
    
    Algorithm:
    1. Verify magic header
    2. Extract salt and nonce
    3. Derive key from password
    4. Decrypt and verify authentication tag
    
    Args:
        blob: Encrypted blob from encrypt_aes_gcm()
        password: Password for decryption
    
    Returns:
        Decrypted plaintext bytes
    
    Raises:
        ValueError: If magic header is invalid, password is wrong, or data is corrupted
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Verify minimum size: magic (4) + salt (16) + nonce (12) + tag (16) = 48 bytes
    min_size = len(MAGIC_HEADER_ENCRYPTED) + SALT_SIZE + NONCE_SIZE + TAG_SIZE
    if len(blob) < min_size:
        raise ValueError("Encrypted data too short")
    
    # Verify magic header
    if blob[:4] != MAGIC_HEADER_ENCRYPTED:
        raise ValueError("Invalid magic header for encrypted data")
    
    logger.info(f"Decrypting {len(blob)} bytes with AES-256-GCM")
    
    pos = 4
    
    # Extract salt
    salt = blob[pos:pos+SALT_SIZE]
    pos += SALT_SIZE
    
    # Extract nonce
    nonce = blob[pos:pos+NONCE_SIZE]
    pos += NONCE_SIZE
    
    # Extract ciphertext (includes tag)
    ciphertext = blob[pos:]
    
    # Derive key
    key = derive_key(password, salt)
    
    # Decrypt and verify
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        logger.info(f"Decryption successful: {len(blob)} → {len(plaintext)} bytes")
        return plaintext
    except Exception as e:
        # Catch any decryption/authentication errors
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Invalid password or corrupted data") from e
