"""Offline validation for the protected Pi publication workflow."""
from __future__ import annotations

import argparse
import ast
import json
import re
import tomllib
from pathlib import Path

CONTEXT = "Post-Merge Release Evidence / Reconcile release evidence"
DESCRIPTION = "POST_MERGE_RELEASE_EVIDENCE_QUALIFIED"


def literal_assignment(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = [
        node.value.value for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
        and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    ]
    if len(values) != 1:
        raise ValueError(f"Expected one literal {name} in {path.name}")
    return values[0]


def validate_versions(root: Path, version: str) -> None:
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-rc\.[0-9]+)?", version) is None:
        raise ValueError("Invalid public release version")
    headings = re.findall(r"^## (.+)$", (root / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE)
    if headings.count(version) != 1:
        raise ValueError("Expected one exact changelog section for requested release")
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != version.replace("-rc.", "rc"):
        raise ValueError("Package version differs from requested release")
    for filename, name in (("__init__.py", "__version__"), ("config.py", "PROTOCOL_VERSION")):
        if literal_assignment(root / "src/djconnect_pi" / filename, name) != version:
            raise ValueError(f"Runtime version differs in {filename}")
    for filename, name in (("install.sh", "DJCONNECT_VERSION"),
                           ("bootstrap_raspberry_pi_os.sh", "DJCONNECT_BOOTSTRAP_VERSION")):
        text = (root / "scripts" / filename).read_text(encoding="utf-8")
        values = re.findall(r'^' + name + r'="\$\{' + name + r':-([^}]+)\}"$', text, re.MULTILINE)
        if values != [version]:
            raise ValueError(f"Installer default differs in {filename}")


def validate_source_status(data: object, candidate_sha: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", candidate_sha) is None:
        raise ValueError("Invalid source commit")
    if not isinstance(data, dict) or data.get("sha") != candidate_sha:
        raise ValueError("Status is not bound to this source commit")
    statuses = data.get("statuses")
    if not isinstance(statuses, list) or any(not isinstance(item, dict) for item in statuses):
        raise ValueError("Invalid current status list")
    matches = [item for item in statuses if item.get("context") == CONTEXT]
    if len(matches) != 1 or matches[0].get("state") != "success" or matches[0].get("description") != DESCRIPTION:
        raise ValueError("Protected post-merge release evidence is not qualified")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    args = parser.parse_args()
    validate_versions(Path(__file__).resolve().parents[1], args.version)
    validate_source_status(json.loads(args.status_file.read_text(encoding="utf-8")), args.candidate_sha)


if __name__ == "__main__":
    main()
