"""Gate a clean committed setup revision in a disposable virtual environment."""

import argparse
import io
import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import uuid
from datetime import datetime, timezone
from pathlib import Path


class GateError(Exception):
    pass


def git(root, *args):
    return subprocess.check_output(
        ["git", "--no-pager", "-C", str(root), *args], text=True,
    ).strip()


def archive(root, destination):
    data = subprocess.check_output(["git", "-C", str(root), "archive", "HEAD"])
    with tarfile.open(fileobj=io.BytesIO(data)) as source:
        for member in source:
            path = destination / member.name
            if not path.resolve().is_relative_to(destination) or not (member.isfile() or member.isdir()):
                raise GateError(f"unsafe archive member: {member.name}")
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as stream:
                    path.write_bytes(stream.read())
                path.chmod(member.mode & 0o777)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, help="new directory for retained logs")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence = (args.evidence_dir or root / ".gate-evidence" / f"seam0-{stamp}-{uuid.uuid4().hex[:8]}").resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    summary = {
        "seam": 0, "started_at": stamp, "python": sys.version,
        "platform": platform.platform(), "steps": [], "result": "FAIL",
        "scope": "offline setup only; no native emulator or AWS verification",
    }

    def step(name, command, cwd, env):
        logfile = evidence / f"{len(summary['steps']) + 1:02d}-{name}.log"
        with logfile.open("w") as stream:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
        passed = result.returncode == 0
        summary["steps"].append({
            "name": name, "result": "PASS" if passed else "FAIL",
            "exit_code": result.returncode, "log": logfile.name,
        })
        print(f"{'PASS' if passed else 'FAIL'} {name}", flush=True)
        if not passed:
            raise GateError(f"{name}: see {logfile}")

    try:
        summary["commit"] = git(root, "rev-parse", "HEAD")
        # The newly allocated evidence directory must be ignored or outside the checkout.
        if git(root, "status", "--porcelain", "--untracked-files=normal"):
            raise GateError("commit or set aside changes before gating; the gate tests HEAD only")
        print("PASS clean-committed-source", flush=True)
        env = {key: value for key, value in os.environ.items() if not key.startswith(("AWS_", "GIT_"))}
        env["GIT_DIR"] = git(root, "rev-parse", "--absolute-git-dir")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        with tempfile.TemporaryDirectory(prefix="odb-seam0-") as directory:
            work = Path(directory)
            source = work / "source"
            source.mkdir()
            archive(root, source)
            env["GIT_WORK_TREE"] = str(source)
            print("PASS disposable-archive", flush=True)
            step("freshness", [sys.executable, "scripts/groom_check.py", "--seam", "0"], source, env)
            step("create-venv", [sys.executable, "-m", "venv", str(work / "venv")], source, env)
            python = str(work / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
            # A fresh venv is intentionally missing the project's declared dependencies.
            probe = subprocess.run(
                [python, "-c", "import boto3, ruff, build, twine, setuptools"],
                cwd=source, env=env, capture_output=True,
            )
            if probe.returncode:
                requirements = tomllib.loads((source / "pyproject.toml").read_text())["build-system"]["requires"]
                step("restore-dependencies", [python, "-m", "pip", "install", ".[dev]", *requirements], source, env)
            step("versions", [python, "-m", "pip", "list", "--format=json"], source, env)
            step("lint", [python, "-m", "ruff", "check", "."], source, env)
            step("offline-tests", [python, "-m", "unittest", "discover", "-s", "tests/unit", "-v"], source, env)
            step("build", [python, "-m", "build", "--no-isolation"], source, env)
            distributions = sorted(source.joinpath("dist").iterdir())
            step("distribution-metadata", [python, "-m", "twine", "check", *(str(p) for p in distributions)], source, env)
            with tarfile.open(next(source.glob("dist/*.tar.gz"))) as package:
                shipped = {"/".join(Path(name).parts[1:]) for name in package.getnames()}
            required = {
                "AGENTS.md", "Makefile", "scripts/groom_check.py", "scripts/gate_seam0.py",
                "scripts/gate-seam0.sh", "docs/design.md", "docs/groom/seam-1-briefs.md",
            }
            if not required <= shipped:
                raise GateError(f"source distribution missing workflow: {sorted(required - shipped)}")
            print("PASS source-workflow-inclusion", flush=True)
            wheel = next(source.glob("dist/*.whl"))
            step("install-wheel", [python, "-m", "pip", "install", "--no-deps", "--force-reinstall", str(wheel)], work, env)
            step("odb-help", [str(Path(python).parent / ("odb.exe" if os.name == "nt" else "odb")), "--help"], work, env)
            step("alias-help", [str(Path(python).parent / ("aws-emulator-shim.exe" if os.name == "nt" else "aws-emulator-shim")), "--help"], work, env)
        summary["result"] = "PASS"
    except (GateError, OSError, subprocess.SubprocessError, tarfile.TarError) as error:
        summary["error"] = str(error)
        print(f"FAIL {error}", flush=True)
    finally:
        summary["finished_at"] = datetime.now(timezone.utc).isoformat()
        (evidence / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"RESULT {summary['result']}\nEvidence: {evidence}", flush=True)
    return 0 if summary["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
