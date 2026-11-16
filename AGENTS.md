# Agent Instructions

`hermes-docker` builds and publishes `ghcr.io/evilcouncil/hermes-docker`, extending `nousresearch/hermes-agent` with OpenCode v2 orchestration capabilities (`opencode-remote` + bundled `opencode-orchestrator` skill) for `EvilCouncil/local_ai_stack`.

## Key Files

| File | Purpose |
|------|---------|
| `Dockerfile` | 3-stage build extending `nousresearch/hermes-agent` with Go, Terraform, npm tools, OpenCode v2, `opencode-remote`, and bundled skill |
| `scripts/opencode-remote` | Wrapper CLI calling `opencode run --attach "$OPENCODE_HOST"` with HTTP Basic Auth (plus `health` and `sessions` subcommands) |
| `skills/software-development/opencode-orchestrator/SKILL.md` | Bundled Hermes skill synced into `/opt/data/skills/` by Hermes's `skills_sync.py` at boot |
| `VERSION` | Pinned `nousresearch/hermes-agent` version (mirrors `HERMES_VERSION`) |
| `update_versions.py` | Queries Docker Hub (`nousresearch/hermes-agent`) and npm (`@opencode/cli`, `pi-*`), updating `Dockerfile` + `VERSION` |
| `test_update_versions.py` | Unit tests for `update_versions.py` |
| `check_build.py` | Checks GHCR tag + GitHub Actions status |

## Commands

```bash
make build            # Build hermes-docker:local
make test             # Run pytest on test_update_versions.py
make update-versions  # Check Docker Hub + npm for updates
make check-build      # Verify GHCR tag + CI status (TAG=v0.23.1)
```

## Patterns & Gotchas

- **Keep `USER root` at the end of `Dockerfile`**: `nousresearch/hermes-agent` uses `s6-overlay` (`/init`), which requires starting as `root` to run `/etc/cont-init.d/01-hermes-setup` (UID remap, `/opt/data` ownership, `skills_sync.py`) before dropping privileges to `hermes` (`s6-setuidgid`). Setting `USER hermes` in `Dockerfile` breaks container boot.
- **Preserve `/opt/hermes/bin` first in `PATH`**: Hermes's privilege-drop shim lives in `/opt/hermes/bin`; always prepend `/opt/hermes/bin:/opt/hermes/.venv/bin:/opt/data/.local/bin` ahead of `/usr/local/go/bin:/npm-global/bin` and keep `/etc/profile.d/zz-opencode-tools.sh` for login shells (`bash -lic`).
- **Isolated workspace**: Hermes keeps its own `/srv/hermes:/opt/data:z` mount and orchestrates repo work remotely inside OpenCode's `/workspace` via `opencode-remote` (`opencode run --attach http://opencode:4096`).
