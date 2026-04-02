# clipboard-relay

Encrypted clipboard relay between machines via git + GPG. Works with any git host.

## Commands

```bash
pip install -e ".[dev]"     # install
pytest                       # test
ruff check src/ tests/       # lint
cb copy "text"               # copy to relay
cb paste                     # paste latest
cb list                      # list clips
cb config --token TOKEN      # configure
```

## Rules

See `.claude/rules/` for detailed rules:
- `architecture.md` — design decisions, data flow, module responsibilities
