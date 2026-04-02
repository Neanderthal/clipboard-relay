"""GPG encrypt/decrypt using python-gnupg."""

from __future__ import annotations

import getpass
import sys

import gnupg


def get_gpg() -> gnupg.GPG:
    return gnupg.GPG()


def encrypt(data: str, recipients: str | list[str]) -> str:
    """Encrypt text with GPG for one or more recipients. Returns ASCII-armored ciphertext."""
    gpg = get_gpg()
    result = gpg.encrypt(data, recipients, armor=True, always_trust=True)
    if not result.ok:
        print(f"GPG encryption failed: {result.status}", file=sys.stderr)
        sys.exit(1)
    return str(result)


def decrypt(armored_data: str, passphrase: str | None = None) -> str:
    """Decrypt ASCII-armored GPG ciphertext."""
    gpg = get_gpg()
    result = gpg.decrypt(armored_data, passphrase=passphrase)
    if not result.ok and passphrase is None:
        # First attempt failed — prompt for passphrase and retry
        passphrase = getpass.getpass("GPG passphrase: ")
        result = gpg.decrypt(armored_data, passphrase=passphrase)
    if not result.ok:
        print(f"GPG decryption failed: {result.status}", file=sys.stderr)
        sys.exit(1)
    return str(result)
