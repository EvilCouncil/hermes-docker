import json
from unittest.mock import MagicMock, patch

import pytest

import update_versions

DOCKERFILE_CONTENT = """\
ARG HERMES_VERSION=0.23.0
ARG HERMES_IMAGE=nousresearch/hermes-agent:v${HERMES_VERSION}

FROM ${HERMES_IMAGE} AS npm-builder

ARG OPENCODE_VERSION=2.2.5
ARG PI_CODING_AGENT_VERSION=1.4.0
ARG PI_SUBAGENTS_VERSION=0.84.0
ARG PI_WEBUI_VERSION=0.11.1
"""


def _urlopen_json(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestFetchers:
    def test_get_latest_hermes_version_ignores_desktop_and_rc_tags(self):
        payload = {
            "results": [
                {"name": "latest"},
                {"name": "v0.24.0-desktop"},
                {"name": "rc.1-v0.24.0"},
                {"name": "v0.23.1"},
                {"name": "v0.23.0"},
            ]
        }
        with patch("urllib.request.urlopen", return_value=_urlopen_json(payload)):
            assert update_versions.get_latest_hermes_version() == "0.23.1"

    def test_get_latest_npm_version_encodes_slash(self):
        captured = []

        def fake_urlopen(url, timeout=None):
            captured.append(url)
            return _urlopen_json({"version": "2.3.0"})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            assert update_versions.get_latest_npm_version("@opencode/cli") == "2.3.0"
        assert "@opencode%2Fcli" in captured[0]


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    dockerfile = tmp_path / "Dockerfile"
    version_file = tmp_path / "VERSION"
    dockerfile.write_text(DOCKERFILE_CONTENT)
    version_file.write_text("0.23.0\n")
    monkeypatch.setattr(update_versions, "DOCKERFILE", dockerfile)
    monkeypatch.setattr(update_versions, "VERSION_FILE", version_file)
    return {"dockerfile": dockerfile, "version_file": version_file}


def mock_latest(
    monkeypatch,
    hermes="0.23.0",
    opencode="2.2.5",
    pi="1.4.0",
    subagents="0.84.0",
    webui="0.11.1",
):
    npm_versions = {
        "@opencode/cli": opencode,
        "@earendil-works/pi-coding-agent": pi,
        "pi-subagents": subagents,
        "@firstpick/pi-package-webui": webui,
    }
    monkeypatch.setattr(update_versions, "get_latest_hermes_version", lambda: hermes)
    monkeypatch.setattr(update_versions, "get_latest_npm_version", lambda pkg: npm_versions[pkg])


class TestMain:
    def test_up_to_date(self, repo, monkeypatch):
        mock_latest(monkeypatch)
        before = repo["dockerfile"].read_text()
        assert update_versions.main() == 0
        assert repo["version_file"].read_text() == "0.23.0\n"
        assert repo["dockerfile"].read_text() == before

    def test_hermes_and_opencode_bumped(self, repo, monkeypatch):
        mock_latest(monkeypatch, hermes="0.23.1", opencode="2.3.0")
        assert update_versions.main() == 0
        assert repo["version_file"].read_text() == "0.23.1\n"
        updated = repo["dockerfile"].read_text()
        assert "ARG HERMES_VERSION=0.23.1" in updated
        assert "ARG OPENCODE_VERSION=2.3.0" in updated

    def test_only_npm_bumped_preserves_version_file(self, repo, monkeypatch):
        mock_latest(monkeypatch, opencode="2.3.0")
        assert update_versions.main() == 0
        assert repo["version_file"].read_text() == "0.23.0\n"
        assert "ARG OPENCODE_VERSION=2.3.0" in repo["dockerfile"].read_text()
