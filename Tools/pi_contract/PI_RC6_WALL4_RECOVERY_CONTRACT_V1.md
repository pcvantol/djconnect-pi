# Pi rc.6 wall-4inch recovery contract

Version: 1. Producer: DJConnect Core. Contract ID: `pi-rc6-wall4-recovery-v1`.
This bounded disposition narrows Peter's selected recovery of the original failed
4-inch deployment. It introduces no new target, privilege, credential, installer,
publication, device action or operational approval. Core owns these normative
bytes; Pi owns the matching consumer and actual readiness/effects/readback.

## Explicit selection, never generic fallback

Use [request schema](PI_RC6_WALL4_RECOVERY_REQUEST_V1.schema.json) and
[manifest schema](PI_RC6_WALL4_RECOVERY_MANIFEST_V1.schema.json), JSON Schema2020-12.
The new manifest is schema_version4, kind
`platform_release_recovery_operational_manifest`, recovery.operation `recover`.
Only the explicitly qualified `.github/workflows/recover-rc6-wall4.yml` may consume
it; the twelve original workflow request inputs retain their transport meaning
(action `deployment`, execution_mode `execute`). Those legacy input literals
are not permission for ordinary deployment. Before any remote effect, enforce
this manifest's discriminator and exact workflow identity in trusted consumer
code. Ordinary deployment and ordinary two-instance smoke/aggregate MUST reject
this recovery manifest/pair; the recovery consumer MUST reject V3, the old pair,
unknown versions, mixed pairs, alternate paths and inferred fallback.

The fixed path is
`docs/release/PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_MANIFEST.json`.
This preparation does NOT create that file or distribute an APPROVED example.
The existing V2 contract, V3 schemas, two-instance rc.6 manifest and all rc.5
history remain byte-identical. Do not repurpose the old operational path.

## Exactly one allowed recovery target

Exactly one required_targets row and one artifact_bindings row are permitted:
`rbpi-djconnect` / `wall-4inch` / `pi-zero-2w-arm64`. The unchanged
[closed inventory](PI_WALL_DEVICE_INVENTORY_V1.json) digest is
`530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0`.
The inventory still contains two physical identities; its Pi10 row conveys no
recovery authority. Reject additional, duplicate, missing, unknown, wrong-profile
or cross-instance rows, even if the otherwise valid inventory contains them.
No wall-10inch action, reinstall, smoke or aggregate carry-forward is permitted.

Publication remains source `0dde0abe22a0859f170a7c1d3eab41f1ade44d37`,
run39658681213, version4.0.0-rc.6 / platform4.0 / INTERNAL_RELEASE, original
versioned Zero archive with hash fixed by both schemas. Consumer source_sha is
separate: it MUST name an actual later protected, qualified matching Pi revision
including its distinct Finalization. Source121/Final122 (2d7a0ee4/7d8758f8) are
component evidence only; they predate adoption of this closed producer contract.
Do not fabricate the future consumer hash or transfer its previous review GO.

## Mandatory semantic authority joins

Schema validation is necessary, never sufficient. The matching consumer MUST:

1. Load exact protected producer contract/schema/inventory and operational
   manifest bytes using explicitly pinned revisions, expected digests and fixed
   paths. Reject duplicate JSON keys, nonfinite numbers, invalid timestamps and
   oversized input. Unknown fields fail closed at every object level.
2. Require actual independent review, applicable exact Owner Authorization,
   normal protected Core source and distinct Finalization, actual canonical
   qualifications, and current human authority for this bounded recovery. An
   APPROVED literal, inventory, schema or chat summary alone grants nothing.
3. Require its own exact protected source and distinct Final qualifications;
   match consumer.source_sha, contract ID, recovery/smoke workflows and smoke
   contract. Publication source is independent, not a required equality to the
   consumer. Both revisions must have their own actual evidence.
4. Match all twelve request inputs to the single manifest/artifact/inventory
   row. Verify actual downloaded original archive bytes, publication provenance,
   installer/lock and80 runtime files. GitHub native immutable is false: versioned
   identity and hash pinning do not claim deletion/replacement protection.
5. Match original failed deployment39669504016, original publication source,
   original Core0b9b4b98 and manifest8740b4c3 to actual retained GitHub provenance:
   completed failure, expected actor and request, intent_dispatched true and
   original actual receipt. Never rewrite that failure as success/cancelled.
6. Check the current latest physical intent, including queued/newer deploy,
   recovery and smoke attempts. Serialize this instance; reject a superseding
   attempt, mixed evidence or an existing claim. No automatic retry/rearm,
   replay, failover or inferred cancellation. Preserve a durable exclusive
   root-owned claim before effects (claim file and parent directories synced).
7. Independently pass canonical deployment readiness, fresh fixed-config digest,
   strict negotiated ed25519 fingerprint, hostname, full model, architecture,
   device profile and fresh boot identity. No caller host/path/user/port override,
   accept-new, sudo rule change, pairing reset, Profile change or new credential.
8. Pin the reviewed helper SHA fixed in recovery.root_helper_sha256. Its bounded
   watchdog hold must be loaded and verified by PID1 before the original sealed
   installer runs once. Preserve configuration/pairing, prior release and all
   original evidence. Require stable API/client, new process identities, exact80
   runtime bytes, original config semantics and boot before restoring only its
   own hold. Failure/timeout leaves uncertain actual state and no implicit retry.

## Separate recovery smoke and truthful result

Successful bounded recovery yields only `RECOVERED_PENDING_SMOKE`.
A distinct read-only `.github/workflows/smoke-rc6-wall4-recovery.yml` implementing
`pi-rc6-wall4-recovery-readback-v1` must match the same original deployment,
recovery run, candidate/artifact, producer pair, manifest ID, consumer,
instance/profile/inventory, helper and current boot/config evidence. Reject
recovery under one consumer with smoke from another. Report expected installed
version/source, process/route health and actual readback; no literal old version.
A matching `SMOKE_PASS` qualifies only this one-instance recovery outcome.
Never emit overall two-instance `DEPLOYMENT_OPERATIONAL`, merge old Pi10 receipts
under a new consumer, or infer physical touch/audio/native/live Session/user
acceptance. Pi10's old actual deployment/smoke evidence remains separate.

## Delivery sequence and unchanged HA

First protect/qualify this producer source and its separate documentary Final.
Then Pi implements explicit adoption and negative tests and protects/qualifies
its own source and separate Final. Only after those actual receipts and fresh
publication/current-authority readback may Core create the separate operational
manifest with the real matching consumer pin, through its own protected source
and separate Final. Only then may the Pi owner evaluate actual readiness and
execute within current authority. No draft grants dispatch.

Core product/HA runtime files are unchanged. After qualification, compare all233
already installed HA-dev files to both new pins and verify actual runtime/HTTP/
SQL plus retained consistent backup; do not restart or reinstall identical code.
No new paid model/API budget or wider device permission follows.
