from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pi_release_candidate", ROOT / "Tools/validate_pi_release_candidate.py")
assert SPEC is not None and SPEC.loader is not None
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)
SHA = "a" * 40


def qualified() -> dict:
    return {"sha": SHA, "statuses": [{"context": candidate.CONTEXT, "state": "success",
                                      "description": candidate.DESCRIPTION}]}


def test_current_versions_and_qualified_status() -> None:
    candidate.validate_versions(ROOT, "4.0.0-rc.6")
    candidate.validate_source_status(qualified(), SHA)


@pytest.mark.parametrize("mutation", ["sha", "missing", "duplicate", "failed", "pending", "description", "malformed"])
def test_source_evidence_fails_closed(mutation: str) -> None:
    data = qualified()
    if mutation == "sha":
        data["sha"] = "b" * 40
    elif mutation == "missing":
        data["statuses"] = []
    elif mutation == "duplicate":
        data["statuses"].append(copy.deepcopy(data["statuses"][0]))
    elif mutation in {"failed", "pending"}:
        data["statuses"][0]["state"] = mutation
    elif mutation == "description":
        data["statuses"][0]["description"] = "NOT_QUALIFIED"
    else:
        data["statuses"] = [None]
    with pytest.raises(ValueError):
        candidate.validate_source_status(data, SHA)


@pytest.mark.parametrize("version", ["4.0.0-rc.5", "4.0.0", "4.0.0rc6", "4.0.0-rc.6\n"])
def test_wrong_requested_version(version: str) -> None:
    with pytest.raises(ValueError):
        candidate.validate_versions(ROOT, version)


@pytest.mark.parametrize("filename,old,new", [
    ("pyproject.toml", 'version = "4.0.0rc6"', 'version = "4.0.0rc5"'),
    ("src/djconnect_pi/__init__.py", '"4.0.0-rc.6"', '"4.0.0-rc.5"'),
    ("src/djconnect_pi/config.py", '"4.0.0-rc.6"', '"4.0.0-rc.5"'),
    ("scripts/install.sh", ":-4.0.0-rc.6", ":-4.0.0-rc.5"),
    ("scripts/bootstrap_raspberry_pi_os.sh", ":-4.0.0-rc.6", ":-4.0.0-rc.5"),
])
def test_each_version_boundary(tmp_path: Path, filename: str, old: str, new: str) -> None:
    for relative in ("CHANGELOG.md", "pyproject.toml", "src/djconnect_pi/__init__.py", "src/djconnect_pi/config.py",
                     "scripts/install.sh", "scripts/bootstrap_raspberry_pi_os.sh"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / relative).read_text(encoding="utf-8")
        target.write_text(text.replace(old, new) if relative == filename else text, encoding="utf-8")
    with pytest.raises(ValueError):
        candidate.validate_versions(tmp_path, "4.0.0-rc.6")



@pytest.mark.parametrize("headings", ["## Unreleased\n", "## 4.0.0-rc.60\n", "## 4.0.0-rc.6\n## 4.0.0-rc.6\n"])
def test_missing_ambiguous_or_prefix_changelog_is_rejected(tmp_path: Path, headings: str) -> None:
    (tmp_path / "CHANGELOG.md").write_text(headings, encoding="utf-8")
    with pytest.raises(ValueError, match="exact changelog"):
        candidate.validate_versions(tmp_path, "4.0.0-rc.6")


def test_publication_waits_for_governance_and_protected_source() -> None:
    workflow = (ROOT / ".github/workflows/publish-release.yml").read_text(encoding="utf-8")
    publish = workflow.split("  publish:\n", 1)[1]
    assert "needs: software-assurance-governance" in publish
    assert "statuses: read" in publish
    assert "fetch-depth: 0" in publish
    assert publish.index("Verify protected source and release versions") < publish.index("Build release assets")
    assert 'git merge-base --is-ancestor "${candidate_sha}" origin/main' in publish
    assert 'commits/${candidate_sha}/status' in publish
    assert 'git rev-parse HEAD > "${dist}/SOURCE_COMMIT"' in publish
    assert publish.index('/SOURCE_COMMIT"') < publish.index('tar -C dist -czf')
