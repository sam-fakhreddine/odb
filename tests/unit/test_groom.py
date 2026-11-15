import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[2] / "scripts" / "groom_check.py"


class GroomCheckTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = {
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
        for key in tuple(self.env):
            if key.startswith("GIT_") and key not in {
                "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL", "GIT_TERMINAL_PROMPT"
            }:
                del self.env[key]
        self.git("init", "-q")
        self.git("config", "core.hooksPath", os.devnull)
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write("docs/design.md", "Contract v1\n")
        self.write("core/rule.py", "value = 1\n")
        self.base = self.commit("baseline")
        self.brief("0", self.base, "docs/design.md")
        self.commit("groom")

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.root, env=self.env, text=True,
            stderr=subprocess.PIPE,
        ).strip()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, title):
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", title)
        return self.git("rev-parse", "HEAD")

    def brief(self, seam, base, dependencies, body="Turn: retain assertions.\n"):
        self.write(
            f"docs/groom/seam-{seam}-briefs.md",
            f"Groomed-at: {base}\nDepends-on: {dependencies}\n\n{body}",
        )

    def check(self, args=(), expected=0, contains=None, cwd=None):
        result = subprocess.run(
            [sys.executable, str(CHECKER), *args], cwd=cwd or self.root,
            env=self.env, text=True, capture_output=True,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, expected, output)
        if contains:
            self.assertIn(contains, output)

    def test_metadata_fails_closed_in_both_modes(self):
        """Catches: malformed or escaping metadata bypassing the gate (fail-closed)."""
        valid = f"Groomed-at: {self.base}\nDepends-on: docs/design.md\n"
        rows = [
            "No headers\n",
            valid.replace("Groomed-at:", "groomed-at:"),
            valid.replace(self.base, "HEAD"),
            valid.replace(self.base, "0" * 40),
            valid.replace("docs/design.md", "../outside"),
            valid.replace("docs/design.md", "/tmp/outside"),
            valid.replace("docs/design.md", ":(glob)**"),
            valid.replace("docs/design.md", "docs/missing.md"),
            valid.replace("docs/design.md", "docs/design.md,"),
        ]
        for number, content in enumerate(rows):
            with self.subTest(row=number):
                self.write("docs/groom/seam-2-briefs.md", content)
                self.commit(f"invalid metadata {number}")
                for args in ((), ("--seam", "0")):
                    self.check(args, expected=1, contains="ERROR")
        self.brief("2", self.base, "docs/design.md")
        self.commit("valid metadata")
        self.check(("--seam", "99"), expected=1, contains="ERROR")
        self.git("checkout", "-q", "--orphan", "other-history")
        self.write("unrelated", "new root\n")
        other = self.commit("unrelated root")
        self.git("checkout", "-q", "-")
        self.brief("2", other, "docs/design.md")
        self.commit("nonancestor metadata")
        self.check(expected=1, contains="ERROR")

    def test_substantive_and_unrelated_paths_have_distinct_verdicts(self):
        """Catches: stale work accepted or unrelated edits blocking another seam."""
        self.check(("--seam", "0"), contains="FRESH")
        self.write("unrelated.md", "Does not affect the seam.\n")
        self.commit("unrelated")
        self.check(("--seam", "0"), contains="FRESH")
        self.write("docs/design.md", "Contract v2\n")
        changed = self.commit("contract changed")
        self.check(contains=changed[:12])
        self.check(("--seam", "0"), expected=1, contains="STALE")
        self.brief("1", changed, "core")
        self.commit("directory dependency")
        self.check(("--seam", "1"), contains="FRESH")
        self.write("core/new.py", "value = 2\n")
        self.commit("new descendant")
        self.check(("--seam", "1"), expected=1, contains="STALE")
        self.write("docs/design.md", "Uncommitted draft\n")
        self.check(("--seam", "0"), expected=1, contains="STALE")

    def test_bookkeeping_does_not_hide_substantive_upstream_changes(self):
        """Catches: header cascades and real changes disguised as bookkeeping."""
        self.brief("1", self.base, "docs/design.md")
        upstream = self.commit("upstream brief")
        self.brief("0", upstream, "docs/groom/seam-1-briefs.md")
        self.commit("groom downstream")
        self.brief(
            "1", upstream, "core",
            body="Re-groomed: 2026-11-15; no turn changes.\nTurn: retain assertions.\n",
        )
        book = self.commit("upstream bookkeeping")
        self.check(("--seam", "0"), contains="FRESH")
        self.brief("1", upstream, "core", body="Turn: changed behavior.\n")
        changed = self.commit("upstream substantive")
        self.check(("--seam", "0"), expected=1, contains="STALE")
        self.brief("0", changed, "docs/groom/seam-1-briefs.md")
        self.commit("regroom downstream")
        self.check(("--seam", "0"), contains="FRESH")
        # A header edit does not erase an earlier substantive change for others.
        self.brief("2", book, "docs/groom/seam-1-briefs.md")
        self.commit("third seam sees old content change")
        self.check(("--seam", "2"), expected=1, contains="STALE")

    def test_history_merges_deletions_and_shallow_bases(self):
        """Catches: merged/deleted dependencies and missing history going green."""
        original = self.git("branch", "--show-current")
        self.git("checkout", "-qb", "side")
        self.write("docs/design.md", "Side contract\n")
        self.commit("side change")
        self.git("checkout", "-q", original)
        self.write("unrelated", "main work\n")
        self.commit("main work")
        self.git("-c", "commit.gpgsign=false", "merge", "--no-ff", "-qm", "merge", "side")
        self.check(("--seam", "0"), expected=1, contains="STALE")
        self.git("rm", "docs/design.md")
        self.commit("removed dependency")
        self.check(expected=1, contains="ERROR")
        self.write("docs/design.md", "Restored\n")
        self.commit("restore")
        shallow = self.root / "shallow"
        self.git("clone", "-q", "--depth=1", "--no-local", self.root.as_uri(), str(shallow))
        self.check(expected=1, contains="ERROR", cwd=shallow)


if __name__ == "__main__":
    unittest.main()
