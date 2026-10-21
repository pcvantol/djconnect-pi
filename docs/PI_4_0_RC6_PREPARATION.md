# Pi 4.0.0-rc.6 preparation

Peter explicitly requested consolidation to main and installation of all latest
Pi changes, including Inter and the shared Glass preference. He separately
selected the same Core owner to prepare the bounded canonical rc.6 contract,
serially after that owner's current change. No new automation window is started.

The source candidate includes both hardware profiles. Existing device identity,
pairing, Profile selection and configuration must be preserved. The official
rc.5 release and historical rc.5 deployment evidence remain immutable.

## Delivery sequence

1. Finish independent exact-source review of PR119, including the Glass/Inter
   delta and final version/consumer changes; resolve concrete findings.
2. Consume only independently read-back protected and canonically qualified Core
   rc.6 source plus separate Finalization. Preserve the historical rc.5 contract;
   no local rewrite of vendored producer schemas or invented target selectors.
3. Qualify the matching Pi consumer, consolidate exact reviewed source through
   protected main, and deliver separate Finalization with post-merge evidence.
4. Publish distinct immutable rc.6 assets for both profiles. Read back actual
   source, versions, package contents, uploaded hashes and publication identity.
5. Obtain the new reviewed/protected Core operative binding for those exact
   published bytes and matching qualified consumer, inventory and human authority.
   The old rc.5 configuration pair or approval cannot authorize rc.6.
6. Use normal qualified per-instance deployment and separate smoke checks with
   current host/device identity checks and configuration preservation/rollback.
7. Capture both actual installed screens. On Pi10 validate Session Flow with real
   Spotify playback on Schuur Denon, reporting actual outcomes and remaining gaps.

## Current boundary

This change prepares version metadata and download examples only. The examples
are future rc.6 URLs, usable after actual publication. No deployment, service
restart, pairing/reset, playback command or real Spotify acceptance is implied.
The existing closed rc.5-only consumer and producer pins remain unchanged until
an actual protected rc.6 handoff is available. Inter and Glass component evidence
on predecessor cf260fb remains component evidence, not rc.6 package qualification.
