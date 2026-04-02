"""Configuration loading from ~/.config/cb/config.toml."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "cb"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_REPO_DIR = CONFIG_DIR / "repo"


@dataclass
class Config:
    repo_url: str  # any git remote URL (gitflic, gitlab, github, etc.)
    gpg_key_id: str
    repo_dir: Path = DEFAULT_REPO_DIR
    clips_dir: str = "clips"

    @classmethod
    def load(cls) -> Config:
        if not CONFIG_FILE.exists():
            print(f"Config not found: {CONFIG_FILE}", file=sys.stderr)
            print("Run: cb config --repo URL --gpg-key KEY_ID", file=sys.stderr)
            sys.exit(1)

        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)

        return cls(
            repo_url=data["repo_url"],
            gpg_key_id=data["gpg_key_id"],
            repo_dir=Path(data.get("repo_dir", str(DEFAULT_REPO_DIR))),
            clips_dir=data.get("clips_dir", "clips"),
        )

    @staticmethod
    def save(
        *,
        repo_url: str | None = None,
        gpg_key: str | None = None,
        repo_dir: str | None = None,
    ) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        existing: dict = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "rb") as f:
                existing = tomllib.load(f)

        if repo_url is not None:
            existing["repo_url"] = repo_url
        if gpg_key is not None:
            existing["gpg_key_id"] = gpg_key
        if repo_dir is not None:
            existing["repo_dir"] = repo_dir

        lines = []
        for key, value in existing.items():
            lines.append(f'{key} = "{value}"')

        CONFIG_FILE.write_text("\n".join(lines) + "\n")
        print(f"Config saved to {CONFIG_FILE}")
