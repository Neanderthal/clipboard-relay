"""CLI entry point for clipboard relay."""

from __future__ import annotations

import sys

import click

from cb.client import GitClient
from cb.config import Config
from cb.crypto import decrypt, encrypt


class SmartGroup(click.Group):
    """Group that treats unknown args as text to copy."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        # If first arg is not a known command and not an option, treat as copy text
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            ctx.ensure_object(dict)
            ctx.obj["copy_text"] = args[0]
            return super().parse_args(ctx, [])
        return super().parse_args(ctx, args)


@click.group(cls=SmartGroup, invoke_without_command=True)
@click.option("--id", "clip_id", default=None, help="Paste a specific clip by filename.")
@click.pass_context
def main(ctx: click.Context, clip_id: str | None) -> None:
    """Encrypted clipboard relay via git.

    \b
    cb "some text"   → copy text to relay
    cb               → paste latest clip
    cb --id FILE     → paste specific clip
    cb list          → list all clips
    cb cleanup       → delete expired clips
    cb config        → show/set configuration
    """
    if ctx.invoked_subcommand is not None:
        return

    copy_text = (ctx.obj or {}).get("copy_text")
    if copy_text is not None:
        _do_copy(copy_text)
    elif not sys.stdin.isatty():
        # Stdin is piped — read and copy
        _do_copy(sys.stdin.read())
    else:
        _do_paste(clip_id)


def _do_copy(text: str) -> None:
    if not text.strip():
        click.echo("Nothing to copy.", err=True)
        sys.exit(1)

    cfg = Config.load()
    encrypted = encrypt(text, cfg.gpg_keys)
    client = GitClient(cfg)
    filename = client.push_clip(encrypted)
    click.echo(f"Copied → {filename}")


def _do_paste(clip_id: str | None) -> None:
    cfg = Config.load()
    client = GitClient(cfg)

    if clip_id:
        content = client.get_clip(clip_id)
    else:
        content = client.get_latest_clip()

    if content is None:
        click.echo("No clips found.", err=True)
        sys.exit(1)

    decrypted = decrypt(content)
    click.echo(decrypted, nl=False)


@main.command("list")
def list_clips() -> None:
    """List all clips in the relay."""
    cfg = Config.load()
    client = GitClient(cfg)
    clips = client.list_clips()

    if not clips:
        click.echo("No clips.")
        return

    for clip in clips:
        age = _format_age(clip.timestamp)
        click.echo(f"  {clip.name}  ({age} ago)")


@main.command()
def cleanup() -> None:
    """Delete clips older than 24 hours."""
    cfg = Config.load()
    client = GitClient(cfg)
    deleted = client.delete_expired()
    if deleted:
        for name in deleted:
            click.echo(f"  Deleted: {name}")
    else:
        click.echo("Nothing to clean up.")


@main.command()
@click.option("--repo", help="Git remote URL (e.g. git@gitflic.ru:user/clipboard.git).")
@click.option("--gpg-key", multiple=True, help="GPG key ID (repeatable for multiple recipients).")
@click.option("--repo-dir", help="Local path for the repo clone.")
def config(repo: str | None, gpg_key: tuple[str, ...], repo_dir: str | None) -> None:
    """Show or set configuration."""
    if not any([repo, gpg_key, repo_dir]):
        try:
            cfg = Config.load()
            click.echo(f"  repo_url:  {cfg.repo_url}")
            click.echo(f"  gpg_keys:  {', '.join(cfg.gpg_keys)}")
            click.echo(f"  repo_dir:  {cfg.repo_dir}")
        except SystemExit:
            pass
        return

    Config.save(
        repo_url=repo,
        gpg_keys=list(gpg_key) if gpg_key else None,
        repo_dir=repo_dir,
    )


def _format_age(ts) -> str:
    from datetime import datetime, timezone

    delta = datetime.now(timezone.utc) - ts
    hours = int(delta.total_seconds() / 3600)
    if hours < 1:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes}m"
    return f"{hours}h"
