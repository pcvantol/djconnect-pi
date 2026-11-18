# CodeQL v4.39.0 Source Finalization

PR127 was normally squash-merged at2026-10-24T16:25:57Z as
`aa581b3f06e654cc56ab698167c64d34714f9be2`, reviewed head
`7003a22c14ed63ec89a36b887425a0ccfe2620be`, base
`6461ab84d903a3bd7e0e27a86f43fd44a0d20c4e`. Reviewed and merged trees match
`98668ad055eda36a284f6033cff035fd81c15168`.

The only source delta replaces CodeQL init/analyze v4.38.3 pins with official
v4.39.0 commit `6f2ac81f5cd81fe351a197ba0b00d91d03cd2aee`. The upstream
annotated tag was independently dereferenced to that commit. Triggers, checkout,
languages and permissions are unchanged. Core Root personally reviewed the
whole workflow and exact two-pin delta: SOURCE_GO_EXACT_ONE_WORKFLOW_TWO_CODEQL_PINS,
findings empty. Exact candidate CI27SUCCESS/4conditionalSKIPPED and canonical
Owner Authorization SUCCESS/Not required LOW_RISK or NORMAL_RISK were read back.
No administrator bypass or self-review was used.

Main Validate40111532258 completed SUCCESS. Original canonical reconciliation
40111694908/artifact12566991704 was actually downloaded:1906bytes, SHA256
`5fc39b49df7d922f2e39942d0f50718cbf7bbac6ca5f47cd5044f20d86739362`.
It binds PR127/head7003a22/mainaa581b3, NORMAL_RISK, no findings and
POST_MERGE_RELEASE_EVIDENCE_QUALIFIED. Original tests, coverage, build, CI,
lint, static analysis, governance and provenance are PASS. The unchanged Pi
canonical status validator independently accepted the actual main status.
Raw/status/receipt evidence is retained under
`/Volumes/Shared Data/tmp/pcvantol/pi-open-pr-merges-20261024`.

Only the existing sole Pi worktree was used; primary checkout, running QA,
paired devices and installed runtime remain unchanged. No new publication,
installation, HA/provider/model action or hardware acceptance is claimed.
PR106 Qt6.12 compatibility remains a separate task. This documentary Final
needs its own independent exact review, normal protected merge and original
postmerge qualification. It creates no new operational deployment authority.
