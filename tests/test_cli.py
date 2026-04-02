"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cb.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_copy_with_arg(runner):
    with patch("cb.cli.Config") as MockConfig, \
         patch("cb.cli.encrypt", return_value="encrypted") as mock_encrypt, \
         patch("cb.cli.GitClient") as MockClient:
        mock_cfg = MagicMock()
        mock_cfg.gpg_keys = ["KEY_A", "KEY_B"]
        MockConfig.load.return_value = mock_cfg
        MockClient.return_value.push_clip.return_value = "20260401_120000.gpg"

        result = runner.invoke(main, ["hello world"])

    assert result.exit_code == 0
    assert "20260401_120000.gpg" in result.output
    mock_encrypt.assert_called_once_with("hello world", ["KEY_A", "KEY_B"])


def test_paste_no_args(runner):
    with patch("cb.cli.Config") as MockConfig, \
         patch("cb.cli.decrypt", return_value="secret text"), \
         patch("cb.cli.GitClient") as MockClient, \
         patch("cb.cli.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        MockConfig.load.return_value = MagicMock()
        MockClient.return_value.get_latest_clip.return_value = "encrypted"

        result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "secret text" in result.output


def test_paste_with_id(runner):
    with patch("cb.cli.Config") as MockConfig, \
         patch("cb.cli.decrypt", return_value="specific text"), \
         patch("cb.cli.GitClient") as MockClient, \
         patch("cb.cli.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        MockConfig.load.return_value = MagicMock()
        MockClient.return_value.get_clip.return_value = "encrypted"

        result = runner.invoke(main, ["--id", "20260401_120000.gpg"])

    assert result.exit_code == 0
    assert "specific text" in result.output


def test_paste_no_clips(runner):
    with patch("cb.cli.Config") as MockConfig, \
         patch("cb.cli.GitClient") as MockClient, \
         patch("cb.cli.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        MockConfig.load.return_value = MagicMock()
        MockClient.return_value.get_latest_clip.return_value = None

        result = runner.invoke(main, [])

    assert result.exit_code != 0
    assert "No clips" in result.output


def test_config_no_args_shows_current(runner):
    mock_cfg = MagicMock()
    mock_cfg.repo_url = "git@gitflic.ru:user/clip.git"
    mock_cfg.gpg_keys = ["ABCD1234", "EFGH5678"]
    mock_cfg.repo_dir = "/home/user/.config/cb/repo"

    with patch("cb.cli.Config") as MockConfig:
        MockConfig.load.return_value = mock_cfg
        result = runner.invoke(main, ["config"])

    assert "gitflic.ru" in result.output
    assert "ABCD1234" in result.output
    assert "EFGH5678" in result.output


def test_config_set_repo(runner):
    with patch("cb.cli.Config") as MockConfig:
        runner.invoke(main, ["config", "--repo", "git@gitflic.ru:user/clip.git"])

    MockConfig.save.assert_called_once_with(
        repo_url="git@gitflic.ru:user/clip.git", gpg_keys=None, repo_dir=None
    )


def test_subcommand_not_treated_as_copy(runner):
    """Ensure 'list', 'cleanup', 'config' are routed to subcommands, not copy."""
    with patch("cb.cli.Config") as MockConfig, \
         patch("cb.cli.GitClient") as MockClient:
        MockConfig.load.return_value = MagicMock()
        MockClient.return_value.list_clips.return_value = []

        result = runner.invoke(main, ["list"])

    assert "No clips." in result.output
