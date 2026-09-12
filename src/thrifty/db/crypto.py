"""Symmetric encryption for secrets held in the database."""

import os
from functools import cache

from cryptography.fernet import Fernet


@cache
def _fernet() -> Fernet:
    # Lazy so importing this module doesn't require the key to be set.
    return Fernet(os.environ["CREDENTIALS_ENCRYPTION_KEY"])


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
