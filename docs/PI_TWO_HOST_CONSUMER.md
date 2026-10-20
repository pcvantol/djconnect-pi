# rc.5 two-instance deployment consumer

This consumer adopts only the protected Core deployment contract source
9b40f422911f08c2076b11e49eb21e98ae5eaa1a, separately finalized by
1328c73e5d35fe13a63910a7bb41e1d0bbdd2d18. The four vendored normative files
are byte pinned in Tools/pi_instance_contract.py. Session product contracts
remain separate. No operational manifest, published asset or installation is
approved by these files.

The three manual workflows accept the original nine fields plus the released
closed instance, hardware profile and inventory digest. They resolve a closed
repository configuration pair PI_RC5_OPERATIONAL_CORE_SHA and
PI_RC5_OPERATIONAL_MANIFEST_SHA256. Both must be supplied together, only after
normal protected consumer qualification, immutable publication and protected
operational approval. The fixed Core path is
`docs/release/PLATFORM_4_0_RC5_PI_OPERATIONAL_MANIFEST.json`. No caller chooses
that path or a private endpoint. Existing v1/RC1 bindings cannot enter this path.

Each run snapshots and validates all source, artifact, inventory, consumer,
publication and per-instance bindings; requires protected-main release evidence
and the canonical readiness action; then opens one fresh strict SSH channel.
The negotiated key and challenge identity must match the approved inventory
before any intent is sent. Fixed SSH aliases also have pinned effective
configuration digests. Child processes receive no GitHub/HA/provider token.
There is one deployment intent, no rerun, retry, fallback or automatic rollback.
A lost acknowledgement records an inconclusive result and possible continuing
remote work; it requires actual state review.

The normal narrow root installer receives sealed, verified profile bytes and
requires an existing configuration. Its strict semantic digest preserves all
configuration fields except release_profile, before activation. Existing
unbound release directories fail closed. Root logs stay private on the target.
A failed installation may leave services stopped; no automatic recovery or
cancellation is claimed. The previous release is retained for an explicitly
reviewed rollback.

A separately dispatched smoke run requires the successful exact deployment run,
checks installed source/version/profile, all packaged runtime bytes, restarted
services and the local API version. It does not pair, select a Profile, call HA,
change display/audio or inject fixtures. Overall operational status requires
both current instance smoke receipts; missing/inconclusive/newer failed results
cannot reuse an older success. Screenshots are a subsequent explicit capture
stage, not part of this smoke acceptance.

## Local qualification, 20 October 2026

236 dedicated offline consumer/installer/installation cases pass with the
separate locked tooling environment. These cover immutable authority, malformed
and cross-instance joins, bounded archive/JSON handling, strict SSH identity,
partial key lines, single intent, uncertain dispatch, private output filtering,
installer rejection before service effects and two-instance aggregation.
Ruff, shell syntax and diff checks pass. The actual existing SSH configuration
was used only for read-only identity/readiness on both targets: wall-4inch rc.3
and wall-10inch rc.4. No installation or service change occurred. These live
observations are not an approved operational manifest or post-deploy smoke.

The application runtime sources remain byte-identical to app source
42dac367a7da88044ba2ca3ac63f73cc86b10346. Its independent bounded Session risk
review closed the queued question P2. This new delivery consumer and installer
need their own exact review and protected CI. Tool tests have their own dedicated
CI dependency lock; default application tests do not silently qualify skipped
tooling tests. Full Apple parity, live Profile/HA, physical touch and installed
rc.5 captures remain open.

An additional six cases prove the private configuration digest changes for any
identity/token/Profile/unknown-field change, ignores only release_profile, and
rejects duplicate/nonfinite/nonobject/malformed/oversize configuration without
private output. The first oversized fixture put its full value into pytest’s
case identifier and exceeded the child environment limit; short explicit case
names correct the harness, with the original failure retained. The restricted
combined run passed1635 with13 socket-permission skips; those skips are not a
product pass. A read-only host check using the actual Shared Data root is MATCH;
the preceding default-old-root DRIFT diagnostic is retained separately.

The loopback-enabled final integrated run passes1648tests with no skips. The
new dedicated workflow initially selected an invalid governance profile `ci`;
the actual canonical check rejected it. It now uses the existing repository
`balanced` CI profile. Release/deployment workflows retain `release`. No policy
is bypassed. The original failure log is retained.
