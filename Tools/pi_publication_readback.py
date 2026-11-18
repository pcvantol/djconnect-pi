"""Read back the pinned Pi 4.0.3-rc.1 publication without device access."""

from __future__ import annotations

import argparse
import hashlib
import json
import os

from Tools.pi_instance_authority import (
    CORE,
    PI,
    PI_ID,
    PUBLICATION,
    PUBLICATION_EVIDENCE_PATH,
    GitHubRead,
    github_file,
    protected_ancestor,
    qualified,
)
from Tools.pi_instance_contract import BindingError, exact_hex, require, strict_json

EVIDENCE_SHA256 = "dc3b6baf00e32f2341b3270a4047e48c8f10fc9166564f6589fa64bf1ba51e28"


def _asset(client, release: dict, asset_id: int, digest: str, maximum: int) -> bytes:
    matches = [asset for asset in release.get("assets", []) if asset.get("id") == asset_id]
    require(len(matches) == 1, "PUBLICATION_ASSET_ID_MISMATCH")
    asset = matches[0]
    size = asset.get("size")
    require(asset.get("state") == "uploaded" and asset.get("digest") == "sha256:" + digest
            and type(size) is int and 0 < size <= maximum, "PUBLICATION_ASSET_METADATA_MISMATCH")
    raw = client.asset(asset_id, maximum)
    require(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest, "ARTIFACT_BYTES_MISMATCH")
    return raw


def _successful_run(client, run_id: int, sha: str, path: str, event: str, error: str) -> None:
    run = client.json(f"repos/{PI}/actions/runs/{run_id}")
    require(run.get("id") == run_id and run.get("repository", {}).get("id") == PI_ID
            and run.get("head_sha") == sha and run.get("head_branch") == "main"
            and run.get("path") == path and run.get("event") == event
            and run.get("status") == "completed" and run.get("conclusion") == "success", error)


def readback(client, core_sha: str) -> dict:
    require(exact_hex(core_sha, 40), "PRODUCER_REFERENCE_INVALID")
    protected_ancestor(client, CORE, core_sha)
    raw, _ = github_file(client, CORE, PUBLICATION_EVIDENCE_PATH, core_sha)
    require(hashlib.sha256(raw).hexdigest() == EVIDENCE_SHA256, "PUBLICATION_EVIDENCE_PIN_MISMATCH")
    evidence = strict_json(raw)
    source, distribution = evidence["source"], evidence["distribution"]
    sha, version = source["source_sha"], evidence["version"]
    qualified(client, PI, sha)

    _successful_run(client, source["post_merge_evidence_run_id"], sha,
                    ".github/workflows/post-merge-release-evidence.yml", "workflow_run", "QUALIFICATION_RUN_MISMATCH")
    _successful_run(client, source["publication_run_id"], sha,
                    source["workflow_path"], "workflow_dispatch", "PUBLICATION_RUN_MISMATCH")

    release = client.json(f"repos/{PUBLICATION}/releases/{distribution['release_id']}")
    require(release.get("id") == distribution["release_id"] and release.get("tag_name") == distribution["release_tag"]
            and release.get("draft") is False and release.get("prerelease") is True
            and release.get("author", {}).get("login") == "djconnect-pi-publisher[bot]", "RELEASE_NOT_PUBLISHED")
    manifest = strict_json(_asset(client, release, distribution["release_manifest_asset_id"],
                                  distribution["release_manifest_sha256"], 262144))
    require(manifest.get("kind") == "djconnect_pi_release_artifact" and manifest.get("schema_version") == 1
            and manifest.get("version") == version and manifest.get("release_tag") == distribution["release_tag"]
            and manifest.get("candidate_sha") == sha and manifest.get("target") == "rbpi-djconnect",
            "PUBLICATION_MANIFEST_MISMATCH")
    profiles = evidence["profiles"]
    require(manifest.get("artifacts") == {
        profile["device_profile"]: {"artifact_id": profile["asset_name"], "artifact_sha256": profile["asset_sha256"]}
        for profile in profiles
    }, "PUBLICATION_PROFILE_MISMATCH")
    for profile in profiles:
        asset = next((row for row in release["assets"] if row.get("id") == profile["asset_id"]), {})
        require(asset.get("name") == profile["asset_name"] and asset.get("browser_download_url") == profile["asset_url"],
                "PUBLICATION_ASSET_METADATA_MISMATCH")
        _asset(client, release, profile["asset_id"], profile["asset_sha256"], 33554432)

    return {
        "classification": "PUBLICATION_READBACK_PASS",
        "core_sha": core_sha,
        "source_sha": sha,
        "release_id": distribution["release_id"],
        "publication_run_id": source["publication_run_id"],
        "profiles": profiles,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-sha", required=True)
    args = parser.parse_args()
    try:
        receipt = readback(GitHubRead(os.environ.get("GH_TOKEN", "")), args.core_sha)
    except BindingError as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
