"""Configuration loading from ~/.config/cb/config.toml."""

from __future__ import annotations

import sys
from dataclasses import dataclass

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "cb"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_REPO_DIR = CONFIG_DIR / "repo"


@dataclass
class Config:
    repo_url: str  # any git remote URL (gitflic, gitlab, github, etc.)
    gpg_keys: list[str]  # one or more GPG key IDs (encrypt to all, any can decrypt)
    repo_dir: Path = DEFAULT_REPO_DIR
    clips_dir: str = "clips"

    @classmethod
    def load(cls) -> Config:
        if not CONFIG_FILE.exists():
            print(f"Config not found: {CONFIG_FILE}", file=sys.stderr)
            print("Run: cb config --repo URL --gpg-key KEY1 --gpg-key KEY2", file=sys.stderr)
            sys.exit(1)

        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)

        # Support both old single-key and new multi-key format
        keys = data.get("gpg_keys", [])
        if not keys and "gpg_key_id" in data:
            keys = [data["gpg_key_id"]]

        return cls(
            repo_url=data["repo_url"],
            gpg_keys=keys,
            repo_dir=Path(data.get("repo_dir", str(DEFAULT_REPO_DIR))),
            clips_dir=data.get("clips_dir", "clips"),
        )

    @staticmethod
    def save(
        *,
        repo_url: str | None = None,
        gpg_keys: list[str] | None = None,
        repo_dir: str | None = None,
    ) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        existing: dict = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "rb") as f:
                existing = tomllib.load(f)

        if repo_url is not None:
            existing["repo_url"] = repo_url
        if gpg_keys is not None:
            existing["gpg_keys"] = gpg_keys
            existing.pop("gpg_key_id", None)  # migrate old format
        if repo_dir is not None:
            existing["repo_dir"] = repo_dir

        lines = []
        for key, value in existing.items():
            if isinstance(value, list):
                items = ", ".join(f'"{v}"' for v in value)
                lines.append(f"{key} = [{items}]")
            else:
                lines.append(f'{key} = "{value}"')

        CONFIG_FILE.write_text("\n".join(lines) + "\n")
        print(f"Config saved to {CONFIG_FILE}")
