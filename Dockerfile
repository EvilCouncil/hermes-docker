ARG HERMES_VERSION=0.23.1
ARG HERMES_IMAGE=nousresearch/hermes-agent:v${HERMES_VERSION}

# Stage 1: install official Go toolchain
FROM ${HERMES_IMAGE} AS go-installer

ARG GO_VERSION=1.26.5
ARG GO_SHA256=5c2c3b16caefa1d968a94c1daca04a7ca301a496d9b086e17ad77bb81393f053

USER root
RUN curl -fsSL -o /tmp/go.tar.gz "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" && \
    echo "${GO_SHA256}  /tmp/go.tar.gz" | sha256sum -c - && \
    tar -C /usr/local -xzf /tmp/go.tar.gz && \
    rm /tmp/go.tar.gz

# Stage 2: install npm packages & OpenCode v2 CLI into /npm-global
FROM ${HERMES_IMAGE} AS npm-builder

ARG OPENCODE_VERSION=2.3.0
ARG PI_CODING_AGENT_VERSION=1.5.2
ARG PI_SUBAGENTS_VERSION=0.88.1
ARG PI_WEBUI_VERSION=0.11.1

USER root
RUN npm install -g --prefix /npm-global \
    @earendil-works/pi-coding-agent@${PI_CODING_AGENT_VERSION} \
    pi-subagents@${PI_SUBAGENTS_VERSION} \
    @firstpick/pi-package-webui@${PI_WEBUI_VERSION} \
    pyright \
    @modelcontextprotocol/server-filesystem \
    mcp-ripgrep

# Install opencode v2 binary directly (used by Hermes via `opencode run --attach`)
RUN mkdir -p /npm-global/bin && \
    curl -fsSL "https://opencode.ai/files/bin/${OPENCODE_VERSION}/opencode-linux-x64.tar.gz" \
        -o /tmp/opencode.tar.gz && \
    tar -xzf /tmp/opencode.tar.gz -C /tmp && \
    mv /tmp/opencode /npm-global/bin/opencode && \
    chmod 755 /npm-global/bin/opencode && \
    rm -rf /tmp/opencode /tmp/opencode.tar.gz && \
    echo "opencode v${OPENCODE_VERSION} installed: $(/npm-global/bin/opencode --version)" && \
    test "$(/npm-global/bin/opencode --version)" = "opencode v${OPENCODE_VERSION}"

# Stage 3: final hermes-agent runtime image with OpenCode orchestration tooling
FROM ${HERMES_IMAGE}

ARG TERRAFORM_VERSION=1.16.5
ARG TERRAFORM_SHA256=2bc2fcfff033265c9e02ca0351f01794eb122f62a9b2a49a3294b9e49eaab5e4

# IMPORTANT: Keep USER root at build end — Hermes uses s6-overlay (/init) which
# requires starting as root to run /etc/cont-init.d/01-hermes-setup (volume setup
# + skills_sync.py) and then drops privileges to user `hermes` via s6-setuidgid.
USER root

RUN apt-get -o Acquire::Retries=3 update && \
    apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
        gh \
        jq \
        python3-pip \
        unzip && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL -o /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" && \
    echo "${TERRAFORM_SHA256}  /tmp/terraform.zip" | sha256sum -c - && \
    unzip /tmp/terraform.zip -d /tmp && \
    mv /tmp/terraform /usr/local/bin/terraform && \
    chmod +x /usr/local/bin/terraform && \
    rm -rf /tmp/terraform.zip

COPY --from=npm-builder /npm-global /npm-global
COPY --from=go-installer /usr/local/go /usr/local/go
COPY scripts/opencode-remote /usr/local/bin/opencode-remote
COPY skills/software-development/opencode-orchestrator/SKILL.md \
     /opt/hermes/skills/software-development/opencode-orchestrator/SKILL.md

RUN chmod 755 /usr/local/bin/opencode-remote && \
    chmod 644 /opt/hermes/skills/software-development/opencode-orchestrator/SKILL.md

# Preserve Hermes PATH precedence (/opt/hermes/bin must remain first for the privilege-drop shim)
# and register in /etc/profile.d so login shells (`bash -lic`) retain Go and /npm-global/bin
ENV PATH="/opt/hermes/bin:/opt/hermes/.venv/bin:/opt/data/.local/bin:/usr/local/go/bin:/npm-global/bin:${PATH}"
RUN printf 'export PATH="/usr/local/go/bin:/npm-global/bin:$PATH"\n' > /etc/profile.d/zz-opencode-tools.sh
