#!/usr/bin/env python3
"""Check Docker Hub (nousresearch/hermes-agent) and npm for latest versions and update Dockerfile and VERSION."""

import json
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent
DOCKERFILE = REPO_ROOT / "Dockerfile"
VERSION_FILE = REPO_ROOT / "VERSION"

NPM_PACKAGES = {
    "@opencode/cli": "OPENCODE_VERSION",
    "@earendil-works/pi-coding-agent": "PI_CODING_AGENT_VERSION",
    "pi-subagents": "PI_SUBAGENTS_VERSION",
    "@firstpick/pi-package-webui": "PI_WEBUI_VERSION",
}


def get_latest_npm_version(package: str) -> str:
    encoded = package.replace("/", "%2F")
    url = f"https://registry.npmjs.org/{encoded}/latest"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())["version"]


def get_latest_hermes_version() -> str:
    url = "https://hub.docker.com/v2/repositories/nousresearch/hermes-agent/tags?page_size=50"
    with urllib.request.urlopen(url, timeout=15) as resp:
        results = json.loads(resp.read()).get("results", [])
    versions: list[tuple[tuple[int, ...], str]] = []
    for item in results:
        name = item.get("name", "")
        m = re.fullmatch(r"v(\d+\.\d+\.\d+)", name)
        if m:
            ver_str = m.group(1)
            versions.append((tuple(int(x) for x in ver_str.split(".")), ver_str))
    if not versions:
        raise RuntimeError("No stable vX.Y.Z tags found for nousresearch/hermes-agent")
    versions.sort(reverse=True)
    return versions[0][1]


def main() -> int:
    content = DOCKERFILE.read_text()

    hermes_match = re.search(r"ARG HERMES_VERSION=(\S+)", content)
    current_hermes = hermes_match.group(1) if hermes_match else None

    current_npm = {}
    for pkg, arg_name in NPM_PACKAGES.items():
        m = re.search(rf"ARG {arg_name}=(\S+)", content)
        current_npm[pkg] = m.group(1) if m else None

    print("Checking Docker Hub and npm for latest versions...")
    latest_hermes = get_latest_hermes_version()
    latest_npm = {pkg: get_latest_npm_version(pkg) for pkg in NPM_PACKAGES}

    changed = False
    if latest_hermes != current_hermes:
        print(f"  nousresearch/hermes-agent: {current_hermes} → {latest_hermes}")
        changed = True
    else:
        print(f"  nousresearch/hermes-agent: {current_hermes} (up to date)")

    for pkg, new_ver in latest_npm.items():
        old_ver = current_npm[pkg]
        if new_ver != old_ver:
            print(f"  {pkg}: {old_ver} → {new_ver}")
            changed = True
        else:
            print(f"  {pkg}: {old_ver} (up to date)")

    if not changed:
        print("\nAll packages up to date.")
        return 0

    if latest_hermes != current_hermes:
        VERSION_FILE.write_text(latest_hermes + "\n")

    content = re.sub(
        r"ARG HERMES_VERSION=\S+",
        f"ARG HERMES_VERSION={latest_hermes}",
        content,
    )
    for pkg, arg_name in NPM_PACKAGES.items():
        content = re.sub(
            rf"ARG {arg_name}=\S+",
            f"ARG {arg_name}={latest_npm[pkg]}",
            content,
        )

    DOCKERFILE.write_text(content)
    print("\nUpdated VERSION and Dockerfile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
