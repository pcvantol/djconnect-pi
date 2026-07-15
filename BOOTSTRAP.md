# DJConnect Pi Repository Bootstrap

This repository owns the Raspberry Pi ambient client and its service/display
runtime. It adopts AI-Native Engineering Operating System 2.2 from
`pcvantol/djconnect/docs/governance/PLATFORM_ARCHITECT_SYSTEM_INSTRUCTIONS.md`
by reference, never by copying central governance.

Start every increment with `git switch main`, `git pull --ff-only`, verification
of current main, clean tree and predecessor PR/history. Read `AGENTS.md`, this
file, rolling records, roadmap and prompt index; reconcile
`MERGED_UNRECONCILED` before work and perform an implementation-reality check.
Lifecycle is `LOCAL_IN_PROGRESS`, `REVIEWABLE_FROZEN`,
`MERGED_UNRECONCILED`, `MERGED_RECONCILED`. Cleanup is fail-closed until merge,
archived history, remote-branch removal and clean tree are proven.
