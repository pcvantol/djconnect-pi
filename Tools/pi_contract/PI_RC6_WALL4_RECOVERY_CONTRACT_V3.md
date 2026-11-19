# Pi rc.6 wall-4inch recovery V3 — exact latest failed attempt

Version: 3. Producer: DJConnect Core. Contract ID `pi-rc6-wall4-recovery-v3`.
This additive producer revision binds the actual latest failed recovery
39775941080. It changes no helper, observer, installer, runtime, root permission,
ledger, hold, pairing or Profile. It is not permission to repeat that recovery.
V1/V2 schemas, operative manifests and original failure evidence remain intact.

## Closed discriminator and separate public indirection

Use [request V3](PI_RC6_WALL4_RECOVERY_REQUEST_V3.schema.json) and
[manifest V3](PI_RC6_WALL4_RECOVERY_MANIFEST_V3.schema.json), JSON Schema2020-12.
The manifest uses schema_version6, unchanged recovery kind and exactly the
`release-4.0.0-rc.6-pi-wall4-recovery-v3-` ID prefix. Its sole fixed future path is
`docs/release/PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_V3_MANIFEST.json`.
This producer does not create that file, an APPROVED specimen, a consumer hash
placeholder, repository variables or a dispatch. The new, separate Pi-owned pair
is `PI_RC6_WALL4_RECOVERY_V3_CORE_SHA` and
`PI_RC6_WALL4_RECOVERY_V3_MANIFEST_SHA256`. Old pairs remain historical.
No fallback, latest lookup, mixed pair, caller-selected path/host/user/port,
ordinary-deployment substitution or implicit retry is permitted.

The twelve request fields retain their exact V2 meanings and constants except
for the new manifest-ID prefix. `action:deployment` and
`execution_mode:execute` remain transport literals for this dedicated recovery
workflow, never ordinary-deployment authority. The dedicated recovery workflow
`.github/workflows/recover-rc6-wall4.yml` and separate
`.github/workflows/smoke-rc6-wall4-recovery.yml` require explicit matching V3
consumer adoption. The smoke contract is `pi-rc6-wall4-recovery-readback-v3`.

## Actual failure and unmodified nested history

The machine-closed `recovery.previous_recovery_attempt` now pins:

- actual workflow run39775941080, workflow_dispatch/main, actorpcvantol,
  attempt1, conclusionfailure, consumer2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a;
- Core83744790decc6ef8940795dc2c9c0e3fb058173b and original operative manifest
  c63ca35c9974b701e70d649a0cbc77a187a2ee83dc329602d6c887a680fcc51d;
- artifact12423814908, name `pi-wall4-recovery-evidence`, member
  `pi-recover-evidence.json`, original3058bytes, SHA256
  `eb57af222e6be4f9d7e9e40be488f3f395ae2e6e94a583e6d4ea7e9d839c6b4d`;
- original kind/schema1/resultRECOVERY_INCONCLUSIVE,
  classificationINCOMPLETE_REQUIRES_ACTUAL_STATE_REVIEW,
  intent_dispatchedtrue and remote_may_still_be_runningtrue;
- the exact original nested V1 previous attempt39695635601, its old consumer,
  Core2945/de22, helper11ce and raw SHAce97876b008d4417ec08100066aa38abf87dd57ae8398ae5e64de97d442744ec.

The original deployment39669504016 and both recoveries stay separately failed.
The consumer independently downloads the original trusted GitHub run metadata
and named artifact, verifies run/head/actor/attempt/workflow/artifact/member,
exact bytes/digest and all declared public joins. Missing or unavailable
original evidence fails closed; no reconstruction, rerun or fabricated receipt.
The nested V1 object must equal the original nested raw object in full.

Top-level `root_helper_sha256` in the previous-attempt descriptor is an exact
code-blob join, not a claim that this field exists in the raw. The V2 raw instead
contains `recovery_helper_sha256`. The original raw has no inputs/action/
execution_mode, root diagnostic, claim-absence or failure-counter fields.
Workflow/actor/attempt/conclusion are trusted run-metadata joins; transport
literals and helper bytes come from the exact pinned consumer workflow/code.
Never manufacture those absent raw fields or infer the exact failed predicate.
A local watchdog/counter observation is a separate point observation, not a new
producer right, permanent readiness or proof of clean completion/cancellation.

## Unchanged scope and final effect guard

Exactly one inventory target remains rbpi-djconnect/wall-4inch/pi-zero-2w-arm64,
inventory SHA530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0.
Publication remains0dde0abe22a0859f170a7c1d3eab41f1ade44d37/run39658681213,
v4.0.0-rc.6/INTERNAL_RELEASE/Zero archive
`d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64`.
The original installer, lock and all80 runtime bytes remain unchanged.
Native immutable:false still requires exact downloaded asset/version/content
joins; it promises no availability or retention guarantee.

Root helper remains
`c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2`;
read-only observer remains
`4ae5b8fa3297785a362dfb2e36354cffb4168ab2d0572ef169288d559239e36c`.
No wait, Timer/MainPID behavior, diagnostic, observation capability, root/sudo
scope, config read body or channel identity is changed by this producer.
The helper must freshly pass its original readiness/model/profile/architecture,
strict ed25519 channel, boot/config/no-competing-installer guards and the
unchanged original exclusive durable ledger claim. All four claim/parent
fsyncs happen before watchdog hold or installer effects. An existing claim
fails closed across changed versions, hashes, manifest IDs and consumers.
Never reset, remove, rename or rearm the ledger, claim or another owner's hold.
Historical claim absence cannot replace the current exclusive create.

Before and after awaits/effects, bind original run/main/actor/attempt1,
provenance, exact consumer, producer pair and current human scope. Evaluate all
four deploy/recovery/ordinary-smoke/recovery-smoke run lists including queued,
newer or competing physical intent. Code, timer, schema validity, new manifest
or pair is never physical replay authority. Unknown state remains inconclusive.
Preserve configuration, pairing, Profile and all failure/guard evidence.
No Pi10, generic/aggregate carry-forward, claim reset, root grant or Root SSH.
Restore only this invocation's verified bounded watchdog guard after actual
healthy exact installed bytes, config semantics and current boot are proven.

## Qualification and operative binding are separate

Current Core consolidation remains one draft PR1290 under Peter's direct
no-merge-until-merge instruction. Draft producer bytes permit read-only matching
consumer preparation; they are not a released source/Final or dispatch gate.
Protect and actually qualify the Core producer through the applicable normal
review/OwnerAuthorization/technical/raw gates only after direct human merge.
Pi then qualifies its actual matching consumer source and separate Final with
negative old/mixed/version/path/failure/helper cases and actual raw receipts.
Only later may a separate Core operative binding pin that actual consumer,
current failure and human scope with its own exact qualifications. No future
consumer placeholder or automatic pair update is part of this producer.
Equal Core product bytes need a fresh exact installed readback, no restart.

Successful recovery is only RECOVERED_PENDING_SMOKE. Separate V3 smoke must
join the same recovery run/consumer/producer pair/helper/observer/original and
latest failure, instance/artifact/boot/config plus exact80files/API/client/
watchdog readback. Matching SMOKE_PASS qualifies only this one instance,
never aggregate DEPLOYMENT_OPERATIONAL or physical/touch/audio/native/user
acceptance. The current human Core timer ends22October19:00UTC/21:00Amsterdam;
it neither extends device authority nor authorizes a retry.
