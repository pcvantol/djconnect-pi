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

## Independent aggregation P1 correction

Core's bounded conformance review rejected reuse of an older smoke after a newer
failed/in-progress deployment. Aggregation now independently reads the latest
relevant deployment for each physical instance, including other manifests and
consumer revisions, and requires completed success plus the exact deployment-run
reference in each smoke. It rechecks both deployment snapshots before reporting
overall success. Missing, truncated, queued, failed, cancelled, timed-out, changed
or unmatched attempts fail overall closed. This is a readback snapshot, not an
atomic cross-workflow lock or permission for another mutation.

Sixteen new two-instance cases cover those later attempts; two additional cases
change deployment during aggregation. The dedicated suite passes254cases. The
full integrated production run after the fix passes1664without skips; its test
collection preceded the last two added race cases, which passed separately in
the254case run. No app, installer, SSH, source rights or actual device changed.
Independent exact fix re-review and protected CI remain required.

The exact fix re-review found a remaining ordering counterexample: a higher-ID
queued intent can have an earlier updated_at than a finishing older deployment.
Deployment intent ordering now uses run ID; inconsistent later updates to an
older run fail closed instead of making it current. The selected latest run must
also have an integer run_attempt exactly1, matching the dispatch controller's
rerun restriction. Four added two-instance cases cover queued higher-ID/earlier
update and same-ID attempt2 with an old smoke. A successful real attempt2 is not
claimed reachable under the current controller; this is an explicit evidence
consistency rejection. Dedicated total258cases; no hardware action.

The rerun fixture now replaces the GitHub run row instead of duplicating its ID.
The independent review correctly identified that the earlier duplicate-row test
could fail through the timestamp guard rather than the attempt guard. Both
same-ID attempt2 tests now demonstrably fail when only the new attempt guard is
removed from an isolated in-memory function copy. Production bytes are unchanged
from93ebce32. Six additional cases reject missing, boolean and string attempts
on both instances.37aggregator/264dedicated cases pass. The exact93eb production
suite passed1670without skips; no newer full-suite count is inferred here.

The same intent-order rule also applies to the other instance's smoke listing:
a higher-ID queued smoke cannot be hidden by an older completion timestamp.
Older runs updated after the newer intent fail closed. One additional negative
case preserves the previous failed/pending protections;38aggregator cases pass.
This is a bounded follow-through of the reviewed ordering defect, without a new
endpoint, mutation, permission or installer change.


## Live authority preflight correction, 20 October 2026

After Core supplied actual qualified operational source bf30bebc, the first
real production resolver rejected its own three-dot ancestor comparison as
traversal. Earlier fake-client tests bypassed GitHubRead.get and missed this
boundary. The corrected reader admits only the exact generated comparison route
for the two fixed repositories and a lowercase forty-character commit. All
other traversal paths remain rejected before HTTP. The comparison requests page
two with one commit, retaining status/merge-base metadata without first-page file
patches, which can exceed the existing bounded metadata reader. Neither metadata
limits nor protected-ancestor, exact qualification or approval checks change.
Actual-opener offline tests cover both repositories, ahead/identical ancestry
and altered comparison/traversal paths. Runtime application bytes, the EADB
candidate and published profile assets are unchanged. The corrected consumer
requires its own protected review/qualification and an exact Core consumer
rebinding before any installation; no direct installer bypass is used.

The final bounded consumer/installer/publication suite passes304 cases, including
18 new reader-boundary regressions; Ruff0.16.0 and diff checks pass. With the
correction, the actual read-only full resolver passes for both existing instance
bindings against qualified Core bf30bebc and published EADB artifacts. This local
corrected-reader result is diagnostic, not protected consumer authority or an
installation. Fresh full-access host verification is MATCH; the preceding
restricted-reader DRIFT result is retained as an access diagnostic.


## Qualified relay tooling preparation correction

The first two actual qualified deployment workflows failed before authority,
readiness, SSH or installation: actions/setup-python attempted to create
/Users/runner/hostedtoolcache/Python on the existing non-hosted macOS relay and
received permission denied. Both original attempts and logs are retained; no
rerun or global tool-cache permission repair is used.

All three instance workflows instead create a fresh run-temp virtual environment
using the relay's already installed /opt/homebrew/bin/python3.14, asserting3.14
and an isolated prefix. GITHUB_PATH exposes that environment only to later steps
in that job. The dependency lock, runtime/installer packages, authority/preflight/
identity/one-intent rules remain unchanged. No global Python, runner service,
credentials or Pi configuration is modified. A new reviewed protected consumer
and exact Core consumer-only rebind are required before a fresh manually
controlled deployment attempt following actual device-state review.

Actual qualified-host execution of all three extracted production shell blocks
passes: fresh3.14.8 virtual environments, isolated prefixes and job-local path
selection. The deployment-created environment installs the exact unchanged lock
and runs304consumer/installer/publication cases successfully. YAML parsing,
Bash syntax and diff checks pass. Fresh strict-key actual read-only state after
both failed preparations confirms wall-4inch stillrc.3 and wall-10inch stillrc.4,
bothTARGET_READY. Those are original-state observations, not installedrc.5.


## Actual worker cache-read isolation

Fresh runs39490525756/39490532326 used the corrected venv setup. The4-inch job
then blocked before output in pip. Read-only sampling and a bounded filename
inspection identified a read-only open of an existing1800byte regular HTTP-cache
metadata file under the shared Core-owned pip cache. No cache contents were read,
no cache permissions/data were changed, and the underlying OS/storage cause is
unproven. The preceding Codex-context lock installation did not qualify this
worker's access context.

The queued10-inch run was cancelled first. Fresh job-stage observations then
confirmed the4-inch authority/install steps were pending with zero start times;
its cancellation completed with both steps skipped. Both actual targets remain
on their originalrc.3/rc.4 releases. No remote installation intent was sent.

All three tooling installs now use pip isolated/no-cache/noninteractive mode and
disable the unrelated version self-check, retaining the exact same lock and binary
only packages. Runtime/app artifacts, authority, identity, readiness, installer,
intent and deployment rules are unchanged. A real worker-context preparation
qualification, separate from installed acceptance, is required before another
protected qualified consumer and exact operational rebind. No old run is rerun.

Preliminary execution of the exact three identical corrected install blocks in a
fresh isolated Codex-context environment installs the same lock and passes304
bounded cases. Bash/YAML/diff checks pass. This is explicitly not worker-context
proof and does not authorize device effects. Both workflows completed cancelled,
both authority/install steps were skipped, the old pip process exited, and the
registered relay returned idle. Those cancellation and process outcomes were
observed independently rather than inferred from the cancellation requests.
