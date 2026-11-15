# Seam 1: Offline evidence contract evidence

Date: 2026-11-15. Tested commit: `911632f4554f4c7ecc8e55fbc4c23a8af0adddaf`.
Environment: macOS ARM64, Python 3.15.1. These are local results, not hosted CI
results and not real AWS or native-emulator verification.

The RED tests (`9d0be61`) produced four assertion failures, one per Done-when
outcome, against callable no-op stubs. The unchanged tests passed with the GREEN
contract (`a5d5d0c`). The complete offline unit suite is 22 tests.

The clean committed-source disposable gate (`make gate-seam1`) passed at the
closure re-groom commit:

| Python | Evidence directory | Result |
| --- | --- | --- |
| 3.15.1 | `seam1-20261115T234036Z-e7011a3d` | PASS |

Seventeen steps passed: freshness, disposable archive, lint, the offline suite,
manifest and evidence structural-schema drift, strict static contracts, build,
distribution metadata, source-workflow inclusion, wheel evidence-contract
inclusion, wheel install, both CLI `--help` entry points and the isolated
installed-wheel manifest-schema, evidence-schema and consumer-type checks.

`schema_version` reuses the exact-integer rule; provenance, outcome, the distinct
assertion outcome, the independent `aws_validation` and `write_state` roundtrip
unchanged, and aggregation never promotes an adapted, unknown, failed or
unconfirmed-observation record to a native AWS-verified pass.

## Scope and limitations

No emulator, native, fixture or AWS operation was run; local validation of a
record is not AWS parity. The local interpreter was 3.15.1, which is outside the
package's declared 3.11-3.14 support matrix and does not re-verify that matrix.
Linux, Windows, hosted CI and real-AWS comparison were not performed here; the
extended schema and typed checks are added to CI separately. Raw per-step logs
and dependency versions remain in the ignored `.gate-evidence/`; this committed
summary is the portable record.
