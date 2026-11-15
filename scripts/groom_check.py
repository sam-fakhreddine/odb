"""Check committed seam briefs against their declared Git dependencies."""

import argparse
import re
import subprocess
from pathlib import PurePosixPath

BRIEF = re.compile(r"docs/groom/seam-(0|[1-9][0-9]*)-briefs\.md")
COMMIT = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
BOOKKEEPING = ("Groomed-at:", "Depends-on:", "Re-groomed:")


class GroomError(Exception):
    pass


def git(*args):
    result = subprocess.run(
        ["git", "--no-pager", *args], text=True, capture_output=True,
    )
    if result.returncode:
        raise GroomError(f"Git failed ({' '.join(args)}): {result.stderr.strip()}")
    return result.stdout


def content(revision, path):
    return git("show", f"{revision}:{path}")


def metadata(path):
    lines = content("HEAD", path).splitlines()
    if len(lines) < 2 or not lines[0].startswith("Groomed-at: ") or not lines[1].startswith("Depends-on: "):
        raise GroomError(f"{path}: first two lines must be Groomed-at and Depends-on")
    base = lines[0].removeprefix("Groomed-at: ")
    if not COMMIT.fullmatch(base):
        raise GroomError(f"{path}: Groomed-at must be a full lowercase commit hash")
    git("cat-file", "-e", f"{base}^{{commit}}")
    git("merge-base", "--is-ancestor", base, "HEAD")
    dependencies = [item.strip() for item in lines[1].removeprefix("Depends-on: ").split(",")]
    if len(set(dependencies)) != len(dependencies):
        raise GroomError(f"{path}: duplicate dependency")
    for dependency in dependencies:
        parts = dependency.split("/")
        if (
            not dependency or PurePosixPath(dependency).is_absolute()
            or any(part in {"", ".", "..", ".git"} for part in parts)
            or any(char in dependency for char in "\\:*?[]\x00\r\n")
        ):
            raise GroomError(f"{path}: dependencies must be literal repository-relative paths")
        git("cat-file", "-e", f"HEAD:{dependency}")
    return base, dependencies


def substantive_lines(text):
    return [line for line in text.splitlines() if not line.startswith(BOOKKEEPING)]


def stale_commits(path, base, dependencies):
    commits = git(
        "log", "--full-history", "--format=%H", f"{base}..HEAD", "--",
        *(f":(literal){dependency}" for dependency in dependencies),
    ).splitlines()
    stale = []
    for commit in dict.fromkeys(commits):
        parents = git("rev-list", "--parents", "-n", "1", commit).split()[1:]
        parent = parents[0] if parents else None
        if parent:
            own_changes = git(
                "diff", "--no-ext-diff", "--no-renames", "--unified=0",
                parent, commit, "--", f":(literal){path}",
            )
            if any(
                line.startswith(("+Groomed-at: ", "-Groomed-at: "))
                for line in own_changes.splitlines()
            ):
                continue
        changed = git(
            "diff-tree", "--root", "--no-commit-id", "-r", "--no-renames",
            "--name-status", "-z", *([parent] if parent else []), commit, "--",
            *(f":(literal){dependency}" for dependency in dependencies),
        ).split("\x00")[:-1]
        for status, name in zip(changed[::2], changed[1::2], strict=True):
            if status == "M" and BRIEF.fullmatch(name) and parent:
                before = substantive_lines(content(parent, name))
                after = substantive_lines(content(commit, name))
                if before == after:
                    continue
            stale.append(commit)
            break
    return stale


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seam", type=int)
    args = parser.parse_args(argv)
    try:
        if git("rev-parse", "--is-shallow-repository").strip() == "true":
            raise GroomError("complete Git history is required; fetch full history first")
        paths = [
            path for path in git("ls-tree", "-r", "--name-only", "HEAD", "--", "docs/groom").splitlines()
            if BRIEF.fullmatch(path)
        ]
        if not paths:
            raise GroomError("no committed docs/groom/seam-N-briefs.md files found")
        selected = f"docs/groom/seam-{args.seam}-briefs.md"
        if args.seam is not None and selected not in paths:
            raise GroomError(f"no committed briefs for seam {args.seam}")
        records = [(path, *metadata(path)) for path in sorted(paths)]
        blocked = False
        for path, base, dependencies in records:
            commits = stale_commits(path, base, dependencies)
            print(f"{'STALE' if commits else 'FRESH'} {path}")
            for commit in commits:
                print(f"  {commit[:12]} {git('show', '-s', '--format=%s', commit).strip()}")
            blocked |= bool(commits) and args.seam is not None and path == selected
        return int(blocked)
    except (GroomError, OSError) as error:
        print(f"ERROR {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
