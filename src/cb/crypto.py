"""GPG encrypt/decrypt using system gpg + gpg-agent."""

from __future__ import annotations

import os
import subprocess
import sys


def encrypt(data: str, recipients: str | list[str]) -> str:
    """Encrypt text with GPG for one or more recipients. Returns ASCII-armored ciphertext."""
    if isinstance(recipients, str):
        recipients = [recipients]
    cmd = ["gpg", "--armor", "--trust-model", "always", "--encrypt"]
    for r in recipients:
        cmd += ["-r", r]
    result = subprocess.run(cmd, input=data, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"GPG encryption failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def decrypt(armored_data: str) -> str:
    """Decrypt ASCII-armored GPG ciphertext. Uses system gpg-agent for passphrase."""
    env = dict(os.environ)
    if "GPG_TTY" not in env:
        try:
            env["GPG_TTY"] = os.ttyname(sys.stdin.fileno())
        except (OSError, AttributeError):
            pass
    result = subprocess.run(
        ["gpg", "--decrypt"],
        input=armored_data, capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        print(f"GPG decryption failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout
