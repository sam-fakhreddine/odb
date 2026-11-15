# ADR 0001: Thin seams and just-in-time grooming

Date: 2026-11-15. Status: accepted for setup.

## Context

The owner supplied "Working in seams, with just-in-time re-grooming" and asked
"ok do the setup". Plans for later features must not drift silently from code.

## Decision

Use the spec/brief/index/handoff layout under `docs/`. Fully groom seam 0
(workflow setup) and seam 1 (the first evidence-contract slice); later features
start as outline rows. Core rules use separate assertion-failing RED and passing
GREEN commits. Each gate keeps evidence and closes with as-built differences.

Briefs begin with `Groomed-at: <full commit>` and `Depends-on: <comma-separated
repository-relative paths>`. Directories include descendants. Check committed
history, not unsaved drafts. Missing/malformed headers, unavailable revisions,
non-ancestor bases and missing dependencies are errors. Report mode warns about
stale briefs and exits zero; `--seam N` gates that seam and exits nonzero when
stale. Malformed briefs fail either mode, even outside the selected seam.

Ignore a commit that moves the checked brief's own `Groomed-at`. For upstream
briefs, ignore only changes to `Groomed-at:`, `Depends-on:` and a single-line
`Re-groomed:` note. Other content changes, additions, deletions and renames are
substantive. Use literal paths, not shell expressions or glob pathspecs.

Before starting stale work, read the dependency commits and actual code,
update turns and tests, advance `Groomed-at`, add a dated `Re-groomed:` note,
commit and rerun. Do not re-groom all future seams after every commit.

## Consequences

The initial checker cannot check itself before it exists. Seam 0 has one
bootstrap exception: commit the spec/brief, prove RED, implement/check GREEN,
then re-groom seam 0 and gate committed code before closing. Future seams
must pass freshness before implementation.

Header-only maintenance does not cascade. Cross-seam findings are recorded
immediately but do not move the downstream grooming baseline. Any result
contradicting an ADR is appended as a dated amendment before code changes.
Human-only rows do not block automated seams and are never represented as
passed. This workflow does not authorize public actions or AWS access.
