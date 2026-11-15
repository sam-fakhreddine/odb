# ODB product contract

ODB (Ol' Dirty Bridge) orchestrates independent local AWS Emulator processes
for tests spanning logical accounts. It owns runtime lifecycle and guarded
clients, selects declared routes and implements explicit bridge operations.
The existing package, CLI, examples and their limitations remain the baseline.

## Promises and limits

- Logical account IDs are metadata, not rewrites of native AWS identity.
- Native API observations, ODB adapters, failures and untested behavior must
  remain distinguishable. Local success is not AWS parity or security proof.
- Generated credentials and private-CA clients target declared loopback
  endpoints. ODB is not an OS network sandbox; unmanaged clients are outside
  that guard.
- Unconfirmed transfers remain attempted, never completed. Cleanup errors
  must not be hidden by success output.
- Role selection is not STS authorization. Event relays, copied objects and
  participant subnet fixtures are not native cross-account delivery, resource
  sharing or packet connectivity.
- Future organization snapshots are explicit logical fixtures, not native
  Organizations membership or SCP enforcement.
- Future trace diagrams represent observed activity, distinguish substitutions
  and unobserved internals, and list outstanding AWS checks. They do not invent
  causality, capture secrets by default or call AWS automatically.
- New features are independently controlled and default off (or manually
  selected for CI). Enabling one must not silently enable another.

## Direction

Establish strict typed inventory contracts first (ADR 0004), then evidence
before growing claims: structured reports, observed traces,
reliable lifecycle, Organizations fixtures, native capability probes, pinned
integration CI and separately authorized AWS comparisons. Retire adapters only
after reviewed native positive and negative controls pass.

The order is a preferred integration order, not a chain of hard dependencies.
Each feature may have several thin seams. Only the next seam is fully groomed.
Runtime production code is unchanged by the seam-workflow setup.

## Owner decisions

- 2026-11-14: "each is a feature branch / flag".
- 2026-11-14: "we also need a way to send in ORG state to emulate an organizations".
- 2026-11-15: "i think i would also like a trace of what calls were made?"
- 2026-11-15: "and it shows where it had to be faked and to check actual aws".
- 2026-11-15: "This is how develop in here", with the supplied
  "Working in seams, with just-in-time re-grooming" workflow.
- 2026-11-15: "ok do the setup".
- 2026-11-15: "while we are early can we do a strongly typed and ZOD style first".

The exact implementation interfaces in future briefs are proposals until
implemented and recorded. This document changes through a recorded decision,
not incidental refactoring.
