# Seam 10: Recorded local evidence

Date: 2026-11-15. Disposable gate tested commit
`0c3183877ca60f8394e70c9d1589ab4c8350b04b` on macOS 27.0.1 ARM64,
Python 3.12.13 and release-please 17.3.0. Result: PASS.

The committed-source gate checked freshness, Ruff, 14 offline unit tests,
release-please behavior, builds, distribution metadata, source-workflow
inclusion and installed-wheel CLI commands. The upstream checks covered 0.x
and 1.x fix, feature and breaking bumps; documentation-only and breaking
changelog entries; project and README version updates; workflow guards; and
the upstream pending-release PR block. The published v0.1.0 tag points at the
configured bootstrap commit. Raw logs are retained locally under ignored
`.gate-evidence/seam0-20261115T205143Z-3da45c3d/`.

The action is pinned to the v4.4.1 **commit**, not the annotated v4 tag object.
The workflow is off for pushes unless explicitly enabled, accepts manual
dispatch on main, requires a separately configured token, and disables GitHub
releases. The existing manual tag and draft-release workflow is unchanged.
After a manual tag, the merged release PR's pending label needs manual removal.

This is a local offline result, not a hosted workflow run. PR creation, token
permissions, CI triggering and the tag/draft-release handoff remain unverified
on GitHub. No push, pull request, tag, release, emulator or AWS call was made.
The gate tested the above commit; this evidence and handoff update follow it.
