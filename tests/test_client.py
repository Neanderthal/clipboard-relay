"""Tests for git-based client."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from cb.client import GitClient
from cb.config import Config


@pytest.fixture
def config(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    return Config(
        repo_url="git@example.com:user/clipboard.git",
        gpg_key_id="ABCD1234",
        repo_dir=repo_dir,
    )


@pytest.fixture
def client_with_repo(config):
    """Client with a fake git repo already initialized."""
    (config.repo_dir / ".git").mkdir()
    clips_dir = config.repo_dir / "clips"
    clips_dir.mkdir()
    client = GitClient(config)
    return client, clips_dir


def test_list_clips_empty(client_with_repo):
    client, clips_dir = client_with_repo
    with patch("cb.client._run"):
        clips = client.list_clips()
    assert clips == []


def test_list_clips_sorted(client_with_repo):
    client, clips_dir = client_with_repo
    (clips_dir / "20260401_100000.gpg").write_text("old")
    (clips_dir / "20260401_120000.gpg").write_text("new")
    (clips_dir / "README.md").write_text("ignore")

    with patch("cb.client._run"):
        clips = client.list_clips()

    assert len(clips) == 2
    assert clips[0].name == "20260401_120000.gpg"
    assert clips[1].name == "20260401_100000.gpg"


def test_get_clip(client_with_repo):
    client, clips_dir = client_with_repo
    (clips_dir / "20260401_120000.gpg").write_text("encrypted-data")

    with patch("cb.client._run"):
        result = client.get_clip("20260401_120000.gpg")

    assert result == "encrypted-data"


def test_get_clip_not_found(client_with_repo):
    client, _ = client_with_repo
    with patch("cb.client._run"):
        with pytest.raises(SystemExit):
            client.get_clip("nonexistent.gpg")


def test_get_latest_clip(client_with_repo):
    client, clips_dir = client_with_repo
    (clips_dir / "20260401_100000.gpg").write_text("old-data")
    (clips_dir / "20260401_120000.gpg").write_text("latest-data")

    with patch("cb.client._run"):
        result = client.get_latest_clip()

    assert result == "latest-data"


def test_get_latest_clip_empty(client_with_repo):
    client, _ = client_with_repo
    with patch("cb.client._run"):
        result = client.get_latest_clip()
    assert result is None


def test_push_clip(client_with_repo):
    client, clips_dir = client_with_repo

    with patch("cb.client._run") as mock_run:
        filename = client.push_clip("encrypted-content")

    assert filename.endswith(".gpg")
    assert (clips_dir / filename).read_text() == "encrypted-content"
    # Should have called git add, commit, push
    assert mock_run.call_count == 4  # pull + add + commit + push


def test_delete_expired(client_with_repo):
    client, clips_dir = client_with_repo
    # Create an old clip (48h ago) and a fresh one
    (clips_dir / "20200101_000000.gpg").write_text("expired")
    now = datetime.now(timezone.utc)
    fresh_name = now.strftime("%Y%m%d_%H%M%S") + ".gpg"
    (clips_dir / fresh_name).write_text("fresh")

    with patch("cb.client._run"):
        deleted = client.delete_expired(max_age_hours=24)

    assert "20200101_000000.gpg" in deleted
    assert fresh_name not in deleted
    assert not (clips_dir / "20200101_000000.gpg").exists()
    assert (clips_dir / fresh_name).exists()
