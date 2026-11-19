# Pi rc.5 two-instance deployment contract

Version: 1. Producer: DJConnect Core. Scope: the already requested rc.5 deployment to the existing 4-inch and 10-inch Pi clients. This is a bounded target-specific extension of [Deployment Input Contract](DEPLOYMENT_INPUT_CONTRACT.md), not a new target family, product feature selection, deployment workflow, artifact publication or operational approval. Consume only a protected exact Core revision after normal source review/checks and separate Finalization. The preserved contextual-DJ WIP and all narrative/native acceptance gates remain separate.

## Canonical target and closed inventory

The canonical target remains exactly `rbpi-djconnect`. Add required `deployment_instance`, `device_profile`, and `inventory_sha256` inputs alongside all nine existing deployment inputs, without changing their meaning. No free host, hostname-derived target, SSH alias as target, port/user/path override, mutable selector, or implicit v1 fallback is allowed.

The [immutable inventory](PI_WALL_DEVICE_INVENTORY_V1.json) contains exactly these reviewed identity bindings:

| deployment_instance | device_profile | endpoint_config_ref | expected hostname |
|---|---|---|---|
| wall-4inch | pi-zero-2w-arm64 | djconnect-wall-4inch | rbpi-djconnect |
| wall-10inch | pi5-arm64 | djconnect-pi10 | rbpi5-djconnect |

These are two physical instances of the same complete Pi client feature target. Hardware presence/common handshake decides local speech/audio availability; this release contract adds no Profile, speech, playback or capability restriction. A `device_profile` is a hardware/package profile, never an application/server Profile or permission.

Each inventory row binds exact architecture, observed board model and negotiated public ed25519 host-key fingerprint. It contains no endpoint address, username, credentials, paired records or server Profile. `endpoint_config_ref` is a closed reference into the matching qualified consumer's fixed protected configuration. Its resolver must be pinned with that consumer; workflow callers cannot supply or retarget its value. Required configuration presence is checked without logging values. A profile-specific credential/endpoint resolver must be qualified before deployment; this contract neither creates configuration nor changes credentials.

The recorded observations were collected read-only by the existing Pi owner with strict existing-host-key checks and no host-key acceptance/update. The source observation digest is provenance, not an authentication or deployment grant. Before each mutation the consumer must independently check the fresh negotiated ed25519 fingerprint against this inventory, then fresh hostname, architecture, complete board-model string and `/etc/djconnect-pi/device-profile`. No accept-new, disabled verification, different known-host key, automatic enrollment or cached observation is a substitute. Any mismatch fails TARGET_NOT_READY before installer/service mutation. Replacing hardware, rotating its key or changing a fixed configuration mapping requires a new reviewed binding and digest.

## Structural schemas and mandatory semantic joins

[Request schema](PI_TWO_HOST_DEPLOYMENT_REQUEST_V2.schema.json) and [manifest schema](PI_TWO_HOST_OPERATIONAL_MANIFEST_V2.schema.json) use JSON Schema2020-12. They close all fields, allowed values, exact rc.5/profile asset identifiers and inventory digest. The new manifest is schema_version2. Existing v1 consumers reject it until explicitly upgraded; historical RC1/RC2 manifests remain immutable and cannot authorize rc.5.

Schema validation is necessary but insufficient. Matching consumers MUST additionally enforce all of these semantic checks before effects:

1. Load the contract, inventory and operational manifest from explicitly approved immutable protected revisions; verify their expected hashes/currentness. Parse bounded JSON with duplicate keys/nonfinite numbers rejected. A caller-supplied document that merely says APPROVED is not authority. Manifest approval must come from the actual protected release process and current human authority, not from this schema or inventory.
2. Match all existing required request inputs to the approved manifest. `candidate_sha` must equal the single Pi repository source_sha, be on qualified protected main, and have matching exact-main release evidence. The published release version is exactly4.0.0-rc.5 and platform4.0/INTERNAL_RELEASE.
3. Match `inventory_id` and the SHA256 of the exact inventory file bytes. Join request target + deployment_instance + device_profile to exactly one inventory row, exactly one required_targets row, and exactly one artifact_bindings row. Duplicate, unknown, partial or ambiguous rows fail closed. The inventory digest does not itself grant permission.
4. Bind the artifact ID, SHA256 and immutable release URL to that same instance/profile/version/source. Cross-profile or generic bundles cannot substitute. Verify actual downloaded artifact bytes and published provenance; reject mutable latest/local-path choices and unknown/stale/superseded manifests. Do not fabricate hash placeholders or approve unpublished bytes.
5. Bind the qualified Pi consumer protected source revision and concrete `pi-rc5-instance-readback-v1` smoke contract. Candidate/artifact and consumer revisions may differ; each requires its own exact protected evidence. Pin schema/contract files independently, without deriving authority from a moving branch.

The release artifact source/publication/digests are intentionally absent from this producer delivery. The final operational manifest is created only after real protected Pi source and publication plus exact approval. No example APPROVED manifest is distributed.

## Readiness, deployment, recovery and smoke

Run the existing canonical deployment-readiness-preflight directly as its separate fail-closed step on the qualified private-network relay, followed by the instance-specific identity/configuration checks above. Schema/inventory publication never satisfies readiness. Readiness and approval are independent per instance; one failed instance does not authorize another or block an independently approved ready instance. Serialize mutations per physical instance; no cross-host failover, automatic retry or operator-free replay.

Use only the qualified GitHub Actions deployment workflow and existing permitted installer. Keep Linux build/publication on qualified build runners and Pi as a runtime target. Preserve configuration, server Profile binding/pairing, prior release and recovery evidence. Timeout or controller cancellation does not prove that a dispatched remote mutation stopped; read its actual state before an explicitly approved recovery. No automatic destructive rollback or privilege/sudo/credential alteration follows from this contract.

Post-deployment smoke is a separate bounded read-only workflow after a successful deployment, bound to the same candidate/artifact/manifest/target/instance/profile/inventory digest/consumer revision and deployment run. It reports the expected version from the binding, never a literal old rc.1. It verifies installed source/package/version, process reachability/startup health and allowed local route readback; optional actual installed-app screenshots retain source/instance/dimensions/hash/time receipts. No fixture injection, server Session start, pairing/reset/Profile selection, HA/service repair, display rotation, speaker or provider action is permitted in smoke. Pi10's unpaired state is honestly labelled; pairing is a separate authorized flow.

Publish one redacted deployment result and one smoke result per instance, including all bound IDs/digests and successful deployment-run reference. Follow [Smoke Policy](POST_DEPLOYMENT_SMOKE_TEST_POLICY.md) result vocabulary, preserving pending/failed/inconclusive states. Overall DEPLOYMENT_OPERATIONAL requires every required instance's successful mutation and matching passing smoke; partial success remains partial. Configuration values, private endpoints, credentials, pairings and bodies remain outside public receipts.

## Matching consumer qualification

Before operational use, Pi qualifies its own fixed configuration resolver, schema+semantic joins, direct canonical preflight, installer/recovery behavior and version-bound smoke. Positive cases cover both exact instances independently. Negative cases cover unknown/missing instance/profile, cross-swapped IDs/digests/assets, duplicates, old schema/RC manifests, changed inventory, free host overrides, host-key/model/profile mismatch, missing config or unready relay, stale/unapproved evidence and wrong-instance/deployment-run smoke. Prove zero mutation on rejection. Source/schema tests, ARM/QML execution, installed deployment, actual screenshots and human/native/hoorbaarheid acceptance are separate evidence classes.

This contract does not issue a new lane/consumer selection or release permission. The existing Pi owner remains the sole Pi writer. Core supplies only this prerequisite; ordinary protected delivery and candidate-bound approval remain required. No HA-dev/prod installation, provider-budget change, credential mutation or hardware action occurs here.
