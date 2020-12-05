"""
Contains crypto-related helper functions.
"""

from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.serialization.base import Encoding
from cryptography.hazmat.primitives.serialization.base import PrivateFormat
from cryptography.hazmat.primitives.serialization.base import PublicFormat
from cryptography.hazmat.primitives.serialization.base import NoEncryption


@dataclass
class CryptoKeyPair:
    private_key: bytes
    public_key: bytes


def genRsaKeyPair(key_size: int = 2048) -> CryptoKeyPair:
    """Generates a new RSA key-pair with the given key size.

    Returns:
        A CryptoKeyPair containing the PEM-encoded keys.
    """
    private_key = rsa.generate_private_key(public_exponent=65537,
                                           key_size=key_size,
                                           backend=backend)

    private_key_bytes = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.TraditionalOpenSSL,  # PKCS#1
        NoEncryption())

    public_key_bytes = private_key.public_key().public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    return CryptoKeyPair(private_key=private_key_bytes,
                         public_key=public_key_bytes)
