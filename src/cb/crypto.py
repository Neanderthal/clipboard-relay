"""GPG encrypt/decrypt using python-gnupg."""

from __future__ import annotations

import sys

import gnupg


def get_gpg() -> gnupg.GPG:
    return gnupg.GPG()


def encrypt(data: str, recipient_key_id: str) -> str:
    """Encrypt text with GPG. Returns ASCII-armored ciphertext."""
    gpg = get_gpg()
    result = gpg.encrypt(data, recipient_key_id, armor=True)
    if not result.ok:
        print(f"GPG encryption failed: {result.status}", file=sys.stderr)
        sys.exit(1)
    return str(result)


def decrypt(armored_data: str) -> str:
    """Decrypt ASCII-armored GPG ciphertext."""
    gpg = get_gpg()
    result = gpg.decrypt(armored_data)
    if not result.ok:
        print(f"GPG decryption failed: {result.status}", file=sys.stderr)
        sys.exit(1)
    return str(result)
