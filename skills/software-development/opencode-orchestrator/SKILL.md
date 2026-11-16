---
name: opencode-orchestrator
description: Delegate repository analysis, code edits, debugging, and software engineering tasks from Hermes to the shared remote OpenCode server (`opencode serve`) using `opencode-remote`.
---

# OpenCode Orchestrator Skill

Hermes runs with its own isolated state and workspace (`/opt/data`), while software repositories live inside the shared **OpenCode** server container (`http://opencode:4096`, mounted at `/workspace` on the OpenCode side and also accessible via OpenChamber).

Whenever you need to inspect codebases in `/workspace`, implement features, run tests, or coordinate coding workflows on the shared OpenCode instance, delegate to OpenCode over the network rather than modifying Hermes's `/opt/data` directory.

## Environment Variables (Preconfigured in Container)

- `OPENCODE_HOST` (default `http://opencode:4096`)
- `OPENCODE_SERVER_USERNAME` (default `opencode`)
- `OPENCODE_SERVER_PASSWORD` (HTTP Basic Auth password)

## Commands

### 1. Verify OpenCode Server Health
```bash
opencode-remote health
```

### 2. List Existing Sessions on OpenCode
```bash
opencode-remote sessions | jq .
```

### 3. Dispatch a Coding Task (One-Shot or Structured JSON)
`opencode-remote` wraps `opencode run --attach "$OPENCODE_HOST" --username "$OPENCODE_SERVER_USERNAME" --password "$OPENCODE_SERVER_PASSWORD"`:

```bash
# Plain text output
opencode-remote "Inspect /workspace and list active repositories and their git status"

# Structured JSON events (recommended when parsing session IDs or tool results)
opencode-remote --format json "Run the test suite in /workspace/<project> and report any failures"
```

### 4. Multi-Turn Session Orchestration
To continue an existing OpenCode session (including sessions visible in OpenChamber or on the user's laptop):

```bash
opencode-remote --session <session_id> "Address the failing unit test and re-run pytest"
```

### 5. Target a Specific Project Directory on the OpenCode Server
Note that `--dir` resolves inside the **OpenCode** container (`/workspace/...`), not inside Hermes:

```bash
opencode-remote --dir /workspace/my-project "Implement the requested API endpoint"
```

## Orchestration Best Practices

1. **Keep workspaces separate**: Store Hermes memories, plans, schedules, and notes in Hermes's own `/opt/data` environment; execute repo mutations via `opencode-remote` so all changes happen cleanly inside OpenCode's `/workspace`.
2. **Scope tasks clearly**: Give OpenCode concrete acceptance criteria, target paths under `/workspace`, and verification commands (e.g., `pytest`, `npm test`, `git status`).
3. **Reuse sessions for iterative work**: Capture the session ID from `opencode-remote sessions` or `--format json` output and pass `--session <id>` for follow-up turns so context is preserved—and so the user can inspect or take over the exact same session in **OpenChamber** or via `opencode attach` from their laptop.
