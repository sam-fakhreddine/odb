"""Check positive consumer types and four intentional errors; optionally use a wheel."""

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path


def check(
    cwd: Path, valid: Path, invalid: Path, config: Path, env: Mapping[str, str],
    *, installed: bool,
) -> int:
    command = [
        sys.executable, "-m", "mypy", "--config-file", str(config),
        "--no-incremental", "--no-pretty", "--no-error-summary", "--show-error-codes",
    ]
    positive = subprocess.run(
        [*command, *([str(valid)] if installed else [])],
        cwd=cwd, env=env, text=True, capture_output=True,
    )
    if positive.returncode:
        print(positive.stdout + positive.stderr)
        return 1
    print("PASS strict positive consumer types")
    negative = subprocess.run(
        [*command, str(invalid)], cwd=cwd, env=env, text=True, capture_output=True,
    )
    codes = re.findall(r"error: .* \[([a-z-]+)\]$", negative.stdout, re.MULTILINE)
    if negative.returncode != 1 or sorted(codes) != [
        "arg-type", "arg-type", "attr-defined", "call-arg",
    ]:
        print("FAIL expected exactly four contract typing errors")
        print(negative.stdout + negative.stderr)
        return 1
    print("PASS four deliberate typing errors rejected")
    runtime = subprocess.run([sys.executable, str(valid)], cwd=cwd, env=env)
    if runtime.returncode:
        return 1
    print("PASS typed consumer runtime roundtrip")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", action="store_true", help="require a typed package in this venv")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "MYPYPATH"}}
    env["PYTHONNOUSERSITE"] = "1"
    if not args.installed:
        return check(
            root, root / "tests/typing/valid.py", root / "tests/typing/invalid.py",
            root / "pyproject.toml", env, installed=False,
        )
    package = importlib.util.find_spec("aws_emulator_shim")
    if package is None or package.origin is None:
        print("FAIL installed typed package not found")
        return 1
    origin = Path(package.origin).resolve()
    if not origin.is_relative_to(Path(sys.prefix).resolve()) or not origin.with_name("py.typed").is_file():
        print("FAIL require an installed wheel with py.typed, not the source checkout")
        return 1
    print("PASS installed wheel type marker and import isolation")
    with tempfile.TemporaryDirectory(prefix="odb-consumer-") as directory:
        consumer = Path(directory)
        for name in ("valid.py", "invalid.py"):
            shutil.copyfile(root / "tests/typing" / name, consumer / name)
        shutil.copyfile(root / "pyproject.toml", consumer / "pyproject.toml")
        return check(
            consumer, consumer / "valid.py", consumer / "invalid.py",
            consumer / "pyproject.toml", env, installed=True,
        )


if __name__ == "__main__":
    raise SystemExit(main())
