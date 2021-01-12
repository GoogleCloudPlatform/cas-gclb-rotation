# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
