"""Git-based client for clipboard relay. Works with any git remote."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cb.config import Config


@dataclass
class Clip:
    name: str
    timestamp: datetime
    path: Path


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    return result


class GitClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.repo_dir = config.repo_dir
        self.clips_path = self.repo_dir / config.clips_dir

    def _ensure_repo(self) -> None:
        """Clone the repo if it doesn't exist, otherwise pull latest."""
        if (self.repo_dir / ".git").exists():
            _run(["git", "pull", "--rebase", "--quiet"], cwd=self.repo_dir)
        else:
            self.repo_dir.mkdir(parents=True, exist_ok=True)
            _run(["git", "clone", self.config.repo_url, str(self.repo_dir)])
        self.clips_path.mkdir(exist_ok=True)

    def push_clip(self, encrypted_content: str) -> str:
        """Write encrypted clip to repo, commit and push. Returns filename."""
        self._ensure_repo()

        now = datetime.now(timezone.utc)
        filename = now.strftime("%Y%m%d_%H%M%S") + ".gpg"
        file_path = self.clips_path / filename

        file_path.write_text(encrypted_content)

        _run(["git", "add", str(file_path)], cwd=self.repo_dir)
        _run(["git", "commit", "-m", f"Add clip {filename}"], cwd=self.repo_dir)
        _run(["git", "push"], cwd=self.repo_dir)

        return filename

    def list_clips(self) -> list[Clip]:
        """List all clips, newest first."""
        self._ensure_repo()

        if not self.clips_path.exists():
            return []

        clips = []
        for f in self.clips_path.iterdir():
            if f.suffix == ".gpg":
                try:
                    ts = datetime.strptime(f.stem, "%Y%m%d_%H%M%S")
                    ts = ts.replace(tzinfo=timezone.utc)
                except ValueError:
                    ts = datetime.now(timezone.utc)
                clips.append(Clip(name=f.name, timestamp=ts, path=f))

        clips.sort(key=lambda c: c.timestamp, reverse=True)
        return clips

    def get_clip(self, filename: str) -> str:
        """Get content of a specific clip."""
        self._ensure_repo()
        file_path = self.clips_path / filename
        if not file_path.exists():
            print(f"Clip not found: {filename}", file=sys.stderr)
            sys.exit(1)
        return file_path.read_text()

    def get_latest_clip(self) -> str | None:
        """Get content of the most recent clip."""
        clips = self.list_clips()
        if not clips:
            return None
        return clips[0].path.read_text()

    def delete_clip(self, filename: str) -> None:
        """Delete a clip, commit and push."""
        file_path = self.clips_path / filename
        if file_path.exists():
            file_path.unlink()
            _run(["git", "add", str(file_path)], cwd=self.repo_dir)

    def delete_expired(self, max_age_hours: int = 24) -> list[str]:
        """Delete clips older than max_age_hours, commit and push."""
        self._ensure_repo()
        clips = self.list_clips()
        now = datetime.now(timezone.utc)
        deleted = []

        for clip in clips:
            age_hours = (now - clip.timestamp).total_seconds() / 3600
            if age_hours > max_age_hours:
                self.delete_clip(clip.name)
                deleted.append(clip.name)

        if deleted:
            _run(["git", "commit", "-m", f"Expire {len(deleted)} clip(s)"], cwd=self.repo_dir)
            _run(["git", "push"], cwd=self.repo_dir)

        return deleted
