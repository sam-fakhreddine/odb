# Developing ODB in seams

Read `docs/design.md`, `docs/groom/index.md`, `docs/handoff.md`, and the active
seam's spec and briefs before editing. Decisions live in `docs/adr/`.

- Work in a dedicated feature branch with independently selectable opt-in
  controls. Preserve existing behavior by default. Do not push, publish, merge,
  release or access real AWS without the owner's authorization.
- Start a seam with `make groom-check SEAM=N` against committed history.
  Never implement stale briefs. Read actual dependency commits and affected
  code, update the brief and its `Groomed-at`, add a dated `Re-groomed:` note,
  commit and check again. Re-groom only the seam that is starting.
- Deliver thin, observable slices. Every Done-when outcome has an acceptance
  test; every turn names a layer, test and test budget before implementation.
- Core logic and trust boundaries use separate RED and GREEN commits from the
  same run. Add a callable no-op stub if necessary so RED fails on assertions,
  not missing imports. Use literal input/expected rows; tests have a `Catches:`
  docstring and name security-relevant properties.
- Glue/configuration is tested after, with recorded evidence. Never loosen,
  skip or delete tests to obtain a pass. Intentional expectation changes must
  be identified in the commit and recorded as a behavior decision.
- Run the seam's disposable gate. Record date, tested commit, environment,
  result and durable evidence reference; close with as-built differences.
  Do not call native/emulated/fixture behavior real AWS proof.
- Amend contradictory ADRs first, adding dated sections rather than rewriting
  history. Feed cross-seam findings into affected future briefs immediately;
  that is not a re-groom. Put unselected ideas in the grooming index.
- List genuinely human-only work in `docs/human-tasks.md`. It does not block
  local seams, but unperformed checks remain explicitly unverified.
- Use conventional commits, one logical change each; scan staged changes for
  secrets before every commit. Update `docs/handoff.md` at session end.

Contributor commands and release safeguards remain in `CONTRIBUTING.md`.
Other agent instruction files, if added, should point here, not duplicate it.
