# Seam 8: Typed inventory evidence

Date: 2026-11-15. Tested commit:
`59768b8873bb748d19ec61c39a830308f53099c9`.
Environment: macOS ARM64. These are local results, not hosted CI results.

The recovered RED tests at `5bcb120ee388` produced 27 assertion failures
across four acceptance methods against callable stubs. The unchanged tests
passed with the GREEN contract at `090819a5c4cb`.

The clean committed-source disposable gate passed for each interpreter:

| Python | Evidence directory | Result |
| --- | --- | --- |
| 3.11.15 | `seam8-20261115T213124Z-df4643a3` | PASS |
| 3.12.13 | `seam8-20261115T213124Z-442d9a5d` | PASS |
| 3.13.15 | `seam8-20261115T213124Z-a715e673` | PASS |
| 3.14.6 | `seam8-20261115T213124Z-7a68e199` | PASS |

Each run checked selected freshness, Ruff, 18 offline tests, generated schema
drift, strict typing and four deliberate type errors, builds, distribution
metadata, wheel contents and isolated installed-wheel consumers. Raw logs and
dependency versions remain in ignored `.gate-evidence/`. The release-please
policy tests also passed separately after reconciling the two gate variants.

Closure documentation follows the tested commit. Strict mode is opt-in; its
schema does not replace semantic validation. No emulator or AWS call, hosted CI,
Linux or Windows verification was performed for this recovery.

## Mapping-key correction after PR 17

Date: 2026-11-15. Tested commit:
`4f90fc95ebdc57292c94830c5bc983547bfb6de3`.
Environment: macOS ARM64, Python 3.12.13.

RED `00141f0` reproduced 12 assertion failures: unmatched account and role
names bypassed both direct model-generated and checked-in schemas. GREEN
`cddacfd` adds `additionalProperties: false` through the two fields' model
metadata and regenerates the schema. The same table now rejects unmatched
names with valid or null values and retains valid names and value validation.
No new test methods or legacy behavior changes were needed.

The first disposable gate stopped on an abbreviated grooming hash, before
running checks. After correcting that metadata, the complete seam-8 gate
passed: `.gate-evidence/seam8-20261115T221359Z-cb0afd45`. It covers offline
tests, lint, schema drift, positive/negative types, builds and installed-wheel
schema/consumer checks. No hosted CI, emulator or AWS verification was run.
