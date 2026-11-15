# Seam 1: Offline evidence contract

Status: groomed ahead 2026-11-15; owner direction: "ok those arte all good",
followed by "each is a feature branch / flag". Not started.
Branch proposal: `feature/run-evidence`. Starts after seam 0.

## Why

A common evidence record must distinguish observation from adaptation before
tracing, capability probes or comparison consumers depend on it. Start with
offline validated records, not all CLI wiring in one change.

## Done when

- A record roundtrips without conflating passed/failed/not-tested outcome with
  native/adapted/unknown provenance or independent AWS validation.
- Aggregation rejects missing/duplicate required checks and cannot call
  adapted or unknown evidence a native pass.
- A failed operation can pass its expected negative-control assertion without
  claiming the operation succeeded; unconfirmed writes remain uncertain.
- Default serialization contains only allowlisted metadata; credentials and
  arbitrary payload fields are rejected, not silently emitted.

Each outcome maps to one table-driven acceptance test method. This slice adds
no network calls, CLI output changes, runtime tracing or AWS validation.

## Turns

| Turn | What | Layer | Test / budget |
| --- | --- | --- | --- |
| 1.0 | Freshness gate and just-in-time re-groom | Docs | `make groom-check SEAM=1` after commit |
| 1.1 | RED callable record/aggregator stubs and literal fixtures | Core | Four tests, one per Done-when line |
| 1.2 | GREEN validation, aggregation and safe serializer | Core | Same four tests |
| 1.3 | Versioned schema/example, disposable offline gate | Glue/docs | Gate validates example and full offline suite |

## Gate

1. Validate committed seam-1 freshness in a clean disposable checkout.
2. Run the four acceptance tables and pre-existing offline unit suite.
3. Validate a synthetic record against the implemented contract and published
   schema; assert explicit missing/unknown cases cannot produce native success.
4. Build/check package and confirm existing CLI help remains available.
5. Retain per-step verdicts, tested SHA and evidence. No emulator/AWS required.

## Progress record

| Date | Turn | Commit | Result |
| --- | --- | --- | --- |
| 2026-11-15 | Ahead grooming | See Git history | Not started; re-groom at start |

## As built

Not implemented. Follow-on evidence seams will wire opt-in CLI reporting,
runtime provenance, partial failure reports and atomic writing independently.

## Feed-forward: 2026-11-15

ADR 0004 inserts typed foundation seam 8 before this seam following the owner's
schema-first direction. At re-groom, replace the standard-library-only proposal
with the established strict Pydantic model/type/schema conventions. Evidence
remains unimplemented; this note does not refresh its stale briefs.
