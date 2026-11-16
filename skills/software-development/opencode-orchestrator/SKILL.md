---
name: opencode-orchestrator
description: Delegate repository analysis, code edits, debugging, and software engineering tasks from Hermes to the shared remote OpenCode v2 server (`opencode serve`) using `opencode-remote`.
---

# OpenCode Orchestrator Skill

Hermes runs with its own isolated state and workspace (`/opt/data`), while software repositories live inside the shared **OpenCode v2** server container (`http://opencode:4096`, mounted at `/workspace` on the OpenCode side and also accessible via OpenChamber).

Whenever you need to inspect codebases in `/workspace`, implement features, run tests, or coordinate coding workflows on the shared OpenCode instance, delegate to OpenCode over the network using `opencode-remote` rather than modifying Hermes's `/opt/data` directory.

## Commands

### 1. Check Server Health & Discover Projects
```bash
# Verify connectivity and authentication to http://opencode:4096
opencode-remote health

# Discover active repositories/projects inside OpenCode's /workspace
opencode-remote projects | jq .
```

### 2. List Existing Sessions for a Repository
```bash
opencode-remote --dir /workspace/EvilCouncil sessions
```

### 3. Dispatch a Coding Task (`opencode run --server`)
Always pass `--dir /workspace/<project>` (matching a directory on the OpenCode server) and `--auto` when running unattended tasks:

```bash
# Plain text output
opencode-remote --dir /workspace/EvilCouncil --auto \
  "Inspect git status and summarize recent commits"

# Structured JSON output (captures session ID and tool events)
opencode-remote --dir /workspace/EvilCouncil --auto --format json \
  "Run the test suite and report any failures"
```

### 4. Continue an Existing Session (Multi-Turn Orchestration)
Pass `--session <session_id>` to continue any session (including sessions visible in OpenChamber or on the user's laptop):

```bash
opencode-remote --dir /workspace/EvilCouncil --auto --session <session_id> \
  "Fix the failing unit test and re-run pytest"
```

### 5. Direct OpenCode v2 REST API Queries
```bash
opencode-remote --dir /workspace/EvilCouncil api GET /api/session | jq .
```

## Orchestration Best Practices

1. **Keep workspaces separate**: Store Hermes memories, plans, schedules, and notes in `/opt/data`; execute repository mutations via `opencode-remote --dir /workspace/<project>` so changes happen cleanly inside OpenCode's `/workspace`.
2. **Scope tasks clearly**: Provide OpenCode concrete acceptance criteria, target paths under `/workspace/<project>`, and verification commands.
3. **Reuse sessions for iterative work**: Capture the `ses_...` ID from `sessions` or `--format json` output and pass `--session <id>` on follow-up turns so context is preserved and visible in **OpenChamber**.
