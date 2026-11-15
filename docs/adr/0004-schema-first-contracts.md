# ADR 0004: Strict schema-first Python contracts before evidence

Date: 2026-11-15. Status: accepted for the typed-contract foundation.

## Context

Owner: "while we are early can we do a strongly typed and ZOD style first".
ODB is a Python package. The owner was unavailable to choose a language/library
when asked; retain Python rather than infer a TypeScript rewrite. This is a
reversible implementation choice, not an owner selection of Pydantic.

## Decision

Use Pydantic 2 models as the source for Python field types, strict boundary
validation and generated JSON Schema. Use mypy strict mode and the Pydantic
plugin for the new contract modules and positive/negative consumer fixtures.
Include a `py.typed` marker in built packages. This does not claim that the
legacy harness, SDK calls or runtime are already statically checked.

Start with the existing account inventory, not speculative evidence, trace or
Organizations models. Require exact types, forbid unknown fields, freeze models
and their nested named mappings, and validate account/port uniqueness and route
references. Parsing must report allowlisted paths/codes, not input values,
validator context or arbitrary payloads. Reject duplicate JSON keys and
non-finite numbers in the file loader rather than silently accepting them.

Provide `Harness(..., strict_manifest=True)` and CLI `--strict-manifest`, both
default off. Existing permissive manifests/API behavior remains available.
Strict parsing is useful independently through the typed public contract API.
Future contracts use this foundation; do not make new features silently active.

JSON Schema describes structural rules; uniqueness across account records,
route-reference integrity and bridge source/target relationships also require
Python semantic validation. Schema-only validation is not sufficient. Generate
the schema from the models and detect drift; do not maintain a parallel schema
by hand. Neither this model nor static checking proves AWS semantics.

## Ordering and consequences

Stable seam numbers are identifiers, not execution order. Add foundation seam
8 after setup and before evidence seam 1. Do not renumber historical seams.
Each future seam re-grooms against the implemented contracts when selected.
Amend the evidence plan's standard-library-only proposal before its execution.

Pydantic is a new bounded runtime dependency; mypy and jsonschema are bounded
development dependencies. The existing Python 3.11-3.14 matrix remains.
Dependency installation is not an emulator or AWS operation. Check structural
schema behavior, runtime rejections, immutable snapshots, type-checker negative
controls, wheel consumer typing and the existing offline suite in the gate.
No push, publication, version bump or AWS execution is authorized here.

## Sources

- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [Model configuration and shallow frozen behavior](https://docs.pydantic.dev/latest/concepts/models/)
- [Validators and JSON Schema limits](https://docs.pydantic.dev/latest/concepts/validators/)
- [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
- [Mypy integration](https://docs.pydantic.dev/latest/integrations/mypy/)

Consulted current official project documentation through Context7 on 2026-11-15.
