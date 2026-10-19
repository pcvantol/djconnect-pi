# Pi 4.0.0-rc.4 preparation

This is a release candidate preparation, not publication or deployment approval.
It follows protected Pi source2d6f8b69cfe6e76ac1dca4eb5c5ac0ccd5201f80 and
Brand V2 producer reconciliation recorded in Pi PR109. No application behavior
is added by the version bump. Public rc.3 already exists as the earlier Pi Zero
device test, so a new candidate must use rc.4 rather than overwrite rc.2/rc.3.

## Candidate identity

Runtime SemVer is4.0.0-rc.4; Python wheel metadata is the equivalent4.0.0rc4.
Installer/bootstrap defaults, runtime protocol metadata and release examples use
the same candidate version. Requirements remain exactly locked; the independent
PySide6.12.0 proposal in PR106 is not absorbed into this candidate. The existing
protected zeroconf0.151.5 and action updates remain present.

The review PR and its package qualification receipt bind the actual candidate
commit, wheel hash, bundle hash and test results. Source preparation is isolated
on its own branch. No tag or public pointer is created by a branch push.

## Physical reference preflight — 19 October 2026

A read-only check of the existing `djconnect-pi10` SSH alias resolves to the actual
Pi5 host `rbpi5-djconnect` (ARM64). Native UI and API services are active; the wall
browser kiosk is inactive. Current release is4.0.0-rc.2/pi5-arm64 with
Python3.13.5 and Qt6.11.1, and103GiB available under the release filesystem.
These observations are a preflight snapshot, not an installation receipt.

The current Pi is unpaired and contains no device credential. A pure settings3
GET therefore returned401. This does not qualify or disqualify the authenticated
HA owner contract. Pairing/Profile selection and subsequent live settings
acceptance remain outstanding. No pairing reset, token replacement or automatic
Profile association was attempted.

An isolated ARM environment must use the candidate's exact Qt6.11.2 lock and
wheel, with synthetic fixture data and a separate configuration. Offscreen ARM
rendering proves package/runtime import and software rendering only; physical
display/touch and actual Session/Profile changes require separate acceptance.
The existing release symlink, services, config, pairing and display remain intact.

## Publication and activation gates

1. Complete exact-candidate package/native qualification and source review.
2. Obtain candidate-specific approval and protected merge with exact-main proof.
3. Publish the exact rc.4 artifacts and immutable manifests only after explicit
   publication approval; never replace an existing version or resolve `latest`.
4. Bind any installation approval to actual Pi5 target, artifact SHA256 and
   protected source. Preserve the current release as rollback material.
5. After authorized activation, verify native UI/API, five-locale rendering,
   display/touch, pairing, six owner-backed choices and restart recovery.

The existing canonical `PLATFORM_4_0_RC1_PI_OPERATIONAL_MANIFEST.json` grants only
an older rc.1 artifact on the Pi Zero `rbpi-djconnect` target. The deployment
workflow's target enum and exact manifest checks do not admit this Pi5 candidate.
Do not reuse that approval, change the target implicitly or dispatch that old
workflow with substituted hashes. A new applicable operational binding is needed
for a governed Pi5 installation. No Core producer/manifest source is changed here.
