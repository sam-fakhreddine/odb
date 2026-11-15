# Seam 8: Typed inventory foundation

Status: locally closed 2026-11-15. Branch: `feature/typed-contracts-main`, based on
current main. Owner direction and implementation choice
are recorded in ADR 0004. Execution order: 0, 8, 1, then the existing outlines.

## Why

Make the current external inventory boundary schema-first before downstream
features grow dictionary contracts. Keep Python and default behavior intact.

## Done when

- Existing example inventories validate, serialize and roundtrip into typed
  models; the generated versioned JSON Schema validates structural fixtures.
- Wrong types (including boolean ports), unknown fields, reserved/duplicate IDs,
  duplicate ports and invalid routes fail before any runtime starts.
- Parsed models and named mappings are immutable snapshots; JSON loading
  rejects duplicate keys, malformed documents and non-finite numbers, without
  echoing rejected values in public validation errors.
- Harness/CLI strict mode is explicitly selected; default legacy behavior is
  unchanged. Positive consumer types pass and deliberate wrong types/fields
  fail static checking, including against an installed wheel outside source.

One table-driven unit test per outcome: budget four new runtime test methods.
Add a positive consumer and one negative file with four predetermined static
errors. Do not expand tests for unrelated legacy behavior.

## Turns

| Turn | Layer | Work / budget |
| --- | --- | --- |
| 8.0 | Docs | ADR and fresh committed brief before core work |
| 8.1 | Core RED | Callable no-op API plus four acceptance tables; assertions fail |
| 8.2 | Core GREEN | Strict models/loader and opt-in boundary; same four tests |
| 8.3 | Glue | Generated schema, strict mypy/negative controls, CI, packaging |
| 8.4 | Gate/docs | Clean disposable gate; record exact tested SHA and limits |

RED and GREEN are separate commits. Glue is tested after; no expectation
loosening. Record additional assertions/implementation discoveries here.

## Gate

Reuse the disposable offline gate, selecting seam 8 freshness rather than
seam 0. Check lint, all offline tests, mypy positive and four negative errors,
schema drift, builds/Twine, packaged contracts/type marker, and installed-wheel
schema/consumer checks outside source. Retain actual dependency versions and
interpreter/platform. Run the existing supported Python matrix locally where
available. No emulator, AWS call or remote publishing belongs to this seam.

## As built

Strict `Account`, `Route` and `Manifest` models, immutable mappings, safe
parsers, generated schema, opt-in Harness/CLI validation and a packaged type
marker were recovered onto current main. Legacy defaults remain unchanged.

Four acceptance methods were run in separate assertion-failing RED and passing
GREEN commits. Schema drift, deliberate type failures and isolated wheel
consumers are checked by CI and the shared disposable gate. See
[local evidence](seam-8-evidence.md); re-groom seam 1 when selected.

## As built

Pending. Evidence reporting, tracing, lifecycle and Organizations remain future
work. The strict gate initially covers new schema/contract code, not all legacy
SDK interactions; future seams must extend it to their typed contracts.
