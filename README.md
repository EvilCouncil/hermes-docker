# 🐳 hermes-docker

Custom **Nous Research Hermes Agent** container image (`nousresearch/hermes-agent`) extended with the **OpenCode v2 CLI**, **`opencode-remote` wrapper**, **`opencode-orchestrator` bundled skill**, Go, Terraform, `gh`, and `pi-coding-agent` so Hermes can act as a high-level orchestrator over a shared `opencode serve` instance while keeping its own `/opt/data` workspace isolated.

📦 **Image:** `ghcr.io/evilcouncil/hermes-docker`

## ✨ What's inside

- 🧠 `nousresearch/hermes-agent` (`s6-overlay` supervised gateway + dashboard + API server)
- 🤖 `opencode` v2 CLI + `/usr/local/bin/opencode-remote` (`opencode run --attach` + `/global/health` + `/session`)
- 📜 Bundled `opencode-orchestrator` skill (`/opt/hermes/skills/software-development/opencode-orchestrator/SKILL.md`), auto-synced into `/opt/data/skills/` on boot
- 🔧 Go `1.26.5`, Terraform `1.16.5`, `gh`, `jq`, `pyright`, MCP servers

## 🔗 Orchestrating OpenCode from Hermes

Pass the OpenCode server connection environment variables to the container:

```yaml
environment:
  OPENCODE_HOST: http://opencode:4096
  OPENCODE_SERVER_USERNAME: opencode
  OPENCODE_SERVER_PASSWORD: ${OPENCODE_SERVER_PASSWORD}
```

Inside Hermes, the `opencode-orchestrator` skill directs coding tasks through `opencode-remote`:

```bash
opencode-remote health
opencode-remote sessions
opencode-remote --dir /workspace/my-repo "Run tests and fix any failing cases"
```
