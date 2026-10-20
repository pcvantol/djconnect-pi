# rc.5 relay tooling correction Finalization

Protected source PR115 merged at2026-10-20T19:51:23Z as
143d21032e46be5f98063bcc908aca1f29e6e66a, tree-identical to independently
reviewed9b8ac1a18823e8420acdb868ac87e396d1a25a74. This separate docs-only
Finalization follows a tree-preserving merge into the existing sole-writer lane.

The original two workflow attempts39485837975/39485843382 failed in setup-python
before authority, readiness, SSH or installation. It attempted an unwritable
/Users/runner/hostedtoolcache/Python. Both failed attempts/logs are retained.
Strict-key actual read-only state then confirmed wall-4inch stillrc.3 and
wall-10inch stillrc.4, bothTARGET_READY. No installation was replayed.

Only the three workflow tooling preparations change: existing absolute Python3.14,
fresh run-temp venv, isolated-prefix check and job-localGITHUB_PATH. Same exact
lock, all authority/readiness/identity/intent gates and app/installer remain.
Actual execution of all three shell blocks succeeds on the qualified relay host;
the deployment-created environment installs the lock and passes304bounded tests.
YAML/Bash/diff checks pass. Core independently executed all three blocks and
issued exact bounded SOURCE GO. Exact source CI27SUCCESS/4conditionalSKIPPED and
fresh HIGH_RISK Owner Authorization39486597487PASS were independently read back.

No global tool-cache permissions, runner service, credentials, pairing, Profile,
HA configuration, app EADB, profile assets or inventory were changed. Fresh
controlled attempts require this separate protected Finalization, actual main
qualification and exact Core consumer-only rebind. Actual installation, separate
smoke, screenshots, live Profile and physical touch remain unclaimed.
