# Architecture

## Overview

clipboard-relay is a personal clipboard sharing tool between two machines.
Clips are GPG-encrypted locally, stored as files in a git repo, and retrieved/decrypted on the other machine.
Works with any git host (GitFlic, GitLab, GitHub, Gitea, etc.).

## Data Flow

```
cb copy "text" → GPG encrypt → write file to local clone → git add + commit + push
cb paste       → git pull → read latest .gpg file → GPG decrypt → stdout
```

## Modules

- `config.py` — loads config from `~/.config/cb/config.toml` (repo URL, GPG key ID, local repo path)
- `crypto.py` — GPG encrypt/decrypt using python-gnupg
- `client.py` — git operations (clone/pull/push) + file CRUD in the `clips/` directory
- `cli.py` — click CLI entry point

## Key Decisions

- **Git as transport** — host-agnostic; no need for host-specific APIs
- **GPG encryption** — E2E; git host only sees ciphertext
- **File-per-clip** — simple, no DB; filename is ISO timestamp
- **1-day expiry** — CI scheduled pipeline or manual `cb cleanup`
- **Web UI (Pages)** — reads a generated `clips.json` manifest; metadata only
- **Local clone** — stored at `~/.config/cb/repo/` by default
