```
      _ _       _                         _                 _
  ___| (_)_ __ | |__   ___   __ _ _ __ __| |      _ __ ___ | | __ _ _   _
 / __| | | '_ \| '_ \ / _ \ / _` | '__/ _` |_____| '__/ _ \| |/ _` | | | |
| (__| | | |_) | |_) | (_) | (_| | | | (_| |_____| | |  __/| | (_| | |_| |
 \___|_|_| .__/|_.__/ \___/ \__,_|_|  \__,_|     |_|  \___||_|\__,_|\__, |
          |_|                                                         |___/
```

**Encrypted clipboard relay between machines via git.**

Copy on one machine, paste on another. End-to-end encrypted with GPG.
Works with **any git host** — GitHub, GitLab, GitFlic, Gitea, self-hosted, whatever.

---

## How It Works

```
Machine A                        Any Git Host                     Machine B
                                (GitHub, GitFlic, etc.)
cb "secret"                                                       cb
    │                                                              │
    ├─ GPG encrypt                                                 ├─ git pull
    ├─ Write to local clone                                        ├─ Read latest .gpg file
    ├─ git commit + push ──────▶  clips/20260402_143052.gpg  ──▶   ├─ GPG decrypt (pinentry)
    │                                                              │
    ▼                                                              ▼
"Copied → 20260402_143052.gpg"                              "secret"
```

- Clips are stored as GPG-encrypted files in a **separate private** data repo
- The git host **never sees plaintext** — only ciphertext
- Each clip is named by UTC timestamp: `YYYYMMDD_HHMMSS.gpg`
- Clips auto-expire after 24 hours (via CI or manual cleanup)
- Uses system `gpg` and `gpg-agent` directly — no Python GPG libraries needed

## Installation

```bash
# From git
git clone https://github.com/Neanderthal/clipboard-relay.git
cd clipboard-relay
pip install .

# Or editable (for development)
pip install -e ".[dev]"
```

## Setup

### 1. Create a data repository

Create a **separate private** repository on your git host. This stores encrypted clips — keep it separate from the tool's source code.

**Important:** Every OS user on each machine that will use `cb` must have **read and write access** to this repository. This means:
- Each user needs their own git credentials (SSH key or HTTPS token) configured
- Each user needs their own `cb config` with their GPG keys
- For shared machines, each user runs `cb config` under their own account

### 2. Set up GPG

Each machine can have its **own GPG key** — no need to share private keys. Clips are encrypted to all configured recipients, so any machine can decrypt with its own key.

```bash
# Generate a key on each machine (if you don't have one)
gpg --full-generate-key

# Find your key ID
gpg --list-keys --keyid-format short
# e.g. Machine A: AAAA1111, Machine B: BBBB2222

# Exchange PUBLIC keys between machines
# On machine A:
gpg --export --armor AAAA1111 > key_a.pub
# Transfer key_a.pub to machine B, then import:
gpg --import key_a.pub

# Do the same in reverse for machine B's public key
```

Passphrase handling is done by the system `gpg-agent` via `pinentry`. If your key has a passphrase, gpg-agent will prompt you using the system's native dialog (GUI or TUI depending on your setup).

### 3. Configure clipboard-relay

Run this on **both machines** with **all** GPG key IDs:

```bash
cb config --repo git@yourhost.com:you/clipboard-data.git \
          --gpg-key AAAA1111 --gpg-key BBBB2222
```

This will:
- Save config to `~/.config/cb/config.toml`
- Clone the data repo to `~/.config/cb/repo/`
- For HTTPS URLs, enable `credential.helper store` so you only enter credentials once

Each clip is encrypted to both keys. Either machine decrypts with its own private key.

### 4. Git authentication

The tool uses `git push/pull` under the hood. Make sure each user can push to the data repo.

**SSH (recommended):**
```bash
ssh -T git@yourhost.com
```

**HTTPS:**
```bash
# Credentials are stored automatically after first use (cb config sets this up)
# If you need to re-enter credentials:
cd ~/.config/cb/repo
git config credential.helper store
git push   # enter username + token, saved for future use
```

**HTTPS with token in URL (no prompts ever):**
```bash
cb config --repo https://oauth2:YOUR_TOKEN@gitflic.ru/project/user/clipboard-data.git \
          --gpg-key AAAA1111 --gpg-key BBBB2222
```

## Usage

```bash
# Copy text (argument)
cb "hello from machine A"

# Copy from stdin (piped input = copy)
echo "piped content" | cb
cat file.txt | cb

# Paste latest clip (no args + interactive terminal = paste)
cb

# Paste into a file
cb > output.txt

# Paste a specific clip
cb --id 20260402_143052.gpg

# List all clips
cb list

# Delete expired clips (older than 24h)
cb cleanup

# Show current config
cb config

# Update config
cb config --repo git@gitflic.ru:user/clips.git
cb config --gpg-key KEY_A --gpg-key KEY_B
cb config --repo-dir /custom/path/to/repo

# Version
cb --version
```

**How `cb` decides copy vs paste:**

| Invocation | Action |
|---|---|
| `cb "text"` | Copy — argument given |
| `echo "text" \| cb` | Copy — stdin is piped |
| `cb` | Paste — no args, interactive terminal |
| `cb --id FILE` | Paste — specific clip |

### Shell aliases for system clipboard integration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# With xsel
alias cbc='xsel --clipboard -o | cb'   # system clipboard → relay
alias cbv='cb | xsel --clipboard -i'   # relay → system clipboard

# With xclip
alias cbc='xclip -selection clipboard -o | cb'
alias cbv='cb | xclip -selection clipboard'

# Wayland
alias cbc='wl-paste | cb'
alias cbv='cb | wl-copy'
```

## Configuration

Config lives at `~/.config/cb/config.toml`:

```toml
repo_url = "git@yourhost.com:you/clipboard-data.git"
gpg_keys = ["AAAA1111", "BBBB2222"]
repo_dir = "/home/you/.config/cb/repo"   # optional, this is the default
```

| Field | Description | Required |
|---|---|---|
| `repo_url` | Git remote URL for the **data** repo | Yes |
| `gpg_keys` | GPG key IDs — encrypt to all, any can decrypt | Yes |
| `repo_dir` | Local path for the repo clone | No (default: `~/.config/cb/repo`) |

## Auto-Cleanup with CI

Clips expire after 24 hours. You can automate cleanup with a scheduled CI pipeline.

### GitLab CI / GitFlic

The repo includes a `.gitlab-ci.yml` that:
- Deploys a web UI to GitLab Pages (shows clip metadata, not content)
- Runs a daily scheduled job to delete expired clips

To enable:
1. Go to your data repo → CI/CD → Schedules
2. Create a daily schedule
3. Add a CI/CD variable `GITLAB_TOKEN` with a project access token

### GitHub Actions

Create `.github/workflows/cleanup.yml` in your **data repo**:

```yaml
name: Cleanup expired clips
on:
  schedule:
    - cron: '0 */6 * * *'  # every 6 hours
  workflow_dispatch:

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          now=$(date +%s)
          deleted=0
          for f in clips/*.gpg; do
            [ -f "$f" ] || continue
            name=$(basename "$f" .gpg)
            file_ts=$(date -d "$(echo $name | sed 's/\(.\{4\}\)\(.\{2\}\)\(.\{2\}\)_\(.\{2\}\)\(.\{2\}\)\(.\{2\}\)/\1-\2-\3 \4:\5:\6/')" +%s 2>/dev/null || echo 0)
            if [ $(( (now - file_ts) / 3600 )) -gt 24 ]; then
              rm "$f"
              git add "$f"
              deleted=$((deleted + 1))
            fi
          done
          if [ "$deleted" -gt 0 ]; then
            git config user.email "ci@clipboard-relay"
            git config user.name "Clipboard Relay CI"
            git commit -m "Expire $deleted clip(s)"
            git push
          fi
```

## Web UI

The repo includes a static web page (`pages/index.html`) that can be deployed via GitLab Pages or GitHub Pages. It shows **metadata only** — timestamps and filenames. Content is GPG-encrypted and can only be read with the CLI.

## Security

| Aspect | Detail |
|---|---|
| **Encryption** | GPG asymmetric encryption via system `gpg` |
| **E2E** | Content encrypted before leaving your machine |
| **At rest** | Git host stores only ciphertext |
| **In transit** | SSH or HTTPS (git transport) |
| **Passphrase** | Handled by system `gpg-agent` + `pinentry` |
| **Web UI** | Metadata only — no decryption possible without GPG key |
| **Expiry** | Clips auto-deleted after 24h via CI |
| **Credentials** | HTTPS credentials cached via `git credential store` |

**The git host never sees your clipboard content.**

## Troubleshooting

| Problem | Fix |
|---|---|
| `terminal prompts disabled` on push | HTTPS credentials not cached. Run `cd ~/.config/cb/repo && git config credential.helper store && git push` and enter credentials once |
| `no secret key` on paste | Import the sender's public key: `gpg --import key.pub` |
| `cannot lock ref HEAD` | Remove stale lock: `rm -f ~/.config/cb/repo/.git/HEAD.lock` |
| `updating unborn branch` on pull | Empty repo — push a clip first, or re-clone: `rm -rf ~/.config/cb/repo && cb config --repo URL` |
| `cb` hangs with no output | Repo not cloned. Run `cb config --repo URL --gpg-key KEY` to clone interactively |
| `%` after paste output | Normal zsh behavior for output without trailing newline |

## Project Structure

```
clipboard-relay/          # Tool source code (public)
├── src/cb/
│   ├── cli.py            # Click CLI — smart routing (arg = copy, no arg = paste)
│   ├── client.py         # Git operations (clone/pull/commit/push)
│   ├── config.py         # Config from ~/.config/cb/config.toml
│   └── crypto.py         # GPG encrypt/decrypt via system gpg
├── pages/
│   └── index.html        # Static web UI for git host Pages
├── tests/
│   ├── test_cli.py
│   ├── test_client.py
│   └── test_crypto.py
├── .gitlab-ci.yml        # GitLab/GitFlic CI config
└── pyproject.toml

clipboard-data/           # Data repo (private, separate)
└── clips/
    ├── 20260402_143052.gpg
    └── ...
```

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
```

## Requirements

- Python 3.8+
- GPG (`gpg`) installed on all machines
- Git with push access to the data repo for **every user** that will use `cb`

## License

MIT
