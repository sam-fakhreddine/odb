Groomed-at: 46f6f776ce6e92622695ac5f5f977c4b8aa759b7
Depends-on: docs/design.md, docs/adr, docs/groom/seam-0-workflow.md
Re-groomed: 2026-11-15; reviewed completed gate and macOS path fix; no further turn changes; closure records local scope and future freshness.

# Seam 0 worker briefs

## 0.1 Documentation

Commit workflow/design decisions and the two fully groomed seams. Keep future
features in the index as outlines. Do not modify runtime behavior or native
integration claims. Test local links and review quoted requirements.

## 0.2 RED checker

Add `scripts/groom_check.py` with callable `main(argv=None)` returning zero,
then four focused table-driven unittest methods in `tests/unit/test_groom.py`.
Use temporary Git repositories with local hooks disabled; no network or
ambient repository writes. Run and record assertion failures, commit RED.

Fixture rows must cover malformed/missing headers and versions, invalid/missing
dependencies, unavailable/non-ancestor bases, selected seam not found,
substantive/unrelated file and directory changes, header-only upstream edits,
substantive upstream changes, own re-grooming, merge history and shallow bases.
Property: invalid metadata cannot bypass the gate; repository-relative literal
paths cannot escape the tree or inject Git pathspecs. Tests contain `Catches:`.

## 0.3 GREEN checker

Read briefs and dependencies at HEAD, validating all metadata before gating.
Use argv-based Git calls, literal pathspecs and full ancestor commits. Report
mode exits zero on stale briefs; selected-seam mode exits one on its stale
briefs. Malformed metadata always fails. Include commits causing staleness.

Own baseline-movement commits are ignored as defined in ADR 0001. For upstream
briefs compare content excluding only the three documented bookkeeping line
prefixes; content changes still count. Do not confuse draft edits with committed
history. Keep code standard-library-only and preserve the RED expectations.

## 0.4 Glue and gate

Add Make commands and a Python disposable gate with a small shell entry point.
Keep current CI check names and the supported Python matrix. Fetch full history
for grooming and run report mode in CI. The selected seam gate enforces its
own freshness; a closed setup seam must not block unrelated future feature CI.
Ensure source distributions retain development docs/scripts; wheel stays library-only.
Document dependencies, evidence retention and dirty/shallow history behavior.

## 0.5 Closure

Read actual changes, re-groom seam 0, commit before running checks and gate.
Record tested SHA, environment, commands, results, durable sanitized evidence,
as-built differences and current handoff. Leave seam 1 stale if appropriate:
do not advance its baseline until it starts. Run reporting check after commits.
Do not push or create a PR as part of this setup without explicit authorization.
