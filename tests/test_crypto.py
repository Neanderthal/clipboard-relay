"""Tests for GPG encrypt/decrypt (subprocess-based)."""

from unittest.mock import patch, MagicMock
import subprocess

import pytest

from cb.crypto import decrypt, encrypt


@patch("cb.crypto.subprocess.run")
def test_encrypt_success(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="-----BEGIN PGP MESSAGE-----\nfoo\n-----END PGP MESSAGE-----",
    )

    result = encrypt("hello", ["ABCD1234", "EFGH5678"])
    assert "PGP MESSAGE" in result
    cmd = mock_run.call_args[0][0]
    assert "-r" in cmd
    assert "ABCD1234" in cmd
    assert "EFGH5678" in cmd


@patch("cb.crypto.subprocess.run")
def test_encrypt_single_recipient(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="encrypted")

    encrypt("hello", "ABCD1234")
    cmd = mock_run.call_args[0][0]
    assert "ABCD1234" in cmd


@patch("cb.crypto.subprocess.run")
def test_encrypt_failure(mock_run):
    mock_run.return_value = MagicMock(returncode=2, stderr="no public key")

    with pytest.raises(SystemExit):
        encrypt("hello", "BADKEY")


@patch("cb.crypto.subprocess.run")
def test_decrypt_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="decrypted text")

    result = decrypt("-----BEGIN PGP MESSAGE-----\nfoo\n-----END PGP MESSAGE-----")
    assert result == "decrypted text"


@patch("cb.crypto.subprocess.run")
def test_decrypt_failure(mock_run):
    mock_run.return_value = MagicMock(returncode=2, stderr="decryption failed")

    with pytest.raises(SystemExit):
        decrypt("bad data")
