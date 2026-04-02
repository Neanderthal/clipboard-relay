"""Tests for GPG encrypt/decrypt."""

from unittest.mock import MagicMock, patch

from cb.crypto import decrypt, encrypt


class FakeGPGResult:
    def __init__(self, ok: bool, data: str = "", status: str = ""):
        self.ok = ok
        self.status = status
        self._data = data

    def __str__(self):
        return self._data


@patch("cb.crypto.get_gpg")
def test_encrypt_success(mock_get_gpg):
    gpg = MagicMock()
    gpg.encrypt.return_value = FakeGPGResult(ok=True, data="-----BEGIN PGP MESSAGE-----\nfoo\n-----END PGP MESSAGE-----")
    mock_get_gpg.return_value = gpg

    result = encrypt("hello", ["ABCD1234", "EFGH5678"])
    assert "PGP MESSAGE" in result
    gpg.encrypt.assert_called_once_with("hello", ["ABCD1234", "EFGH5678"], armor=True)


@patch("cb.crypto.get_gpg")
def test_encrypt_failure(mock_get_gpg):
    gpg = MagicMock()
    gpg.encrypt.return_value = FakeGPGResult(ok=False, status="no public key")
    mock_get_gpg.return_value = gpg

    import pytest
    with pytest.raises(SystemExit):
        encrypt("hello", "BADKEY")


@patch("cb.crypto.get_gpg")
def test_decrypt_success(mock_get_gpg):
    gpg = MagicMock()
    gpg.decrypt.return_value = FakeGPGResult(ok=True, data="decrypted text")
    mock_get_gpg.return_value = gpg

    result = decrypt("-----BEGIN PGP MESSAGE-----\nfoo\n-----END PGP MESSAGE-----")
    assert result == "decrypted text"


@patch("cb.crypto.get_gpg")
def test_decrypt_failure(mock_get_gpg):
    gpg = MagicMock()
    gpg.decrypt.return_value = FakeGPGResult(ok=False, status="decryption failed")
    mock_get_gpg.return_value = gpg

    import pytest
    with pytest.raises(SystemExit):
        decrypt("bad data")
