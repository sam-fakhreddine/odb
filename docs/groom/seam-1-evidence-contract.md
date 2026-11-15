# Seam 1: Offline evidence contract

Status: implemented locally on `feature/run-evidence` 2026-11-15 for
`sam-fakhreddine/odb#8`; contract slice only. Branch: `feature/run-evidence`.
Re-groomed just in time against typed seam 8 before implementation.

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
| 2026-11-15 | 1.0 Re-groom | `3318a8d` | FRESH `make groom-check SEAM=1` |
| 2026-11-15 | 1.1 RED | `9d0be61` | 4 assertion failures against callable stubs |
| 2026-11-15 | 1.2 GREEN | `a5d5d0c` | 4 acceptance tests pass; 22 offline tests pass |
| 2026-11-15 | 1.3 Gate | see [evidence](seam-1-evidence.md) | Disposable offline gate |

## As built

Implemented as strict Pydantic contracts reusing the seam-8 `StrictContract`
configuration rather than the earlier standard-library-only proposal (ADR 0004).
`aws_emulator_shim/evidence.py` provides `EvidenceRecord` (single-token
identifiers and operation labels; independent `outcome`,
`native`/`adapted`/`unknown` provenance, an `assertion` outcome kept distinct
from the operation, an independent `aws_validation` state and a `write_state`),
`parse_evidence_record` (strict, hidden-input diagnostics shaped like
`ManifestError`), `aggregate_evidence` (complete and uniquely identified checks,
separate native/adapted/unknown pass counts, uncertain writes and
`native_verified` only for AWS-confirmed native passes) and
`evidence_json_schema`. `schema.py` gained a `--model evidence` mode so the
generated `docs/schemas/evidence-v1.schema.json` and the synthetic
`docs/schemas/evidence-v1.example.json` stay drift-checked.

Behavior decision: the schema and example were placed in `docs/schemas/`
(co-located with `manifest-v1.schema.json`) rather than the provisional
`docs/evidence-v1.schema.json` path named in the ahead-groomed plan, for
consistency with the already-merged typed-contract layout. `parse_evidence_record`
rejects credential/payload/diagnostic fields as unexpected extras and never
discloses a rejected value; `schema_version` reuses the exact-integer rule.

This slice changes no CLI output, makes no network or AWS calls and enables no
runtime feature. Follow-on evidence seams will wire opt-in CLI reporting,
runtime provenance, partial failure reports and atomic writing independently.

## Feed-forward: 2026-11-15

Field names and semantics to reuse downstream: `check_id` as the stable
per-check key, `outcome`/`assertion` separation, the
`native`/`adapted`/`unknown` provenance vocabulary and the independent
`aws_validation` (`not_checked`/`confirmed`/`unconfirmed`) and `write_state`
(`not_applicable`/`confirmed`/`unconfirmed`) states. Tracing (feature 2),
Organizations (feature 4), capability probes (feature 5) and CI (feature 6)
must emit records through this contract and must not infer AWS confirmation
from local success or promote adapted/unknown observations to native passes.
Evidence IDs here are contract labels, not execution proof.

## Feed-forward: 2026-11-15

ADR 0004 inserts typed foundation seam 8 before this seam following the owner's
schema-first direction. At re-groom, replace the standard-library-only proposal
with the established strict Pydantic model/type/schema conventions. Evidence
remains unimplemented; this note does not refresh its stale briefs.
