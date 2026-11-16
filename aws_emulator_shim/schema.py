"""Generate or check the structural schema; semantic rules need parse_manifest."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import JsonValue

from .contracts import Manifest
from .evidence import evidence_json_schema


def manifest_json_schema() -> dict[str, JsonValue]:
    schema: dict[str, JsonValue] = Manifest.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:odb:manifest:1"
    schema["$comment"] = (
        "Structural validation only. Also use parse_manifest for unique logical "
        "account IDs/ports, declared route accounts and distinct bridge endpoints."
    )
    return schema


SCHEMAS = {"manifest": manifest_json_schema, "evidence": evidence_json_schema}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", type=Path, help="fail if a schema differs from the model")
    mode.add_argument("--output", type=Path, help="write schema instead of printing it")
    parser.add_argument(
        "--model", choices=sorted(SCHEMAS), default="manifest",
        help="contract model to generate or check (default: manifest)",
    )
    args = parser.parse_args(argv)
    generated = json.dumps(SCHEMAS[args.model](), indent=2, sort_keys=True) + "\n"
    if args.check:
        if args.check.read_text(encoding="utf-8") != generated:
            print(f"FAIL {args.model} schema drift; regenerate with --output")
            return 1
        print(f"PASS {args.model} schema matches models")
    elif args.output:
        args.output.write_text(generated, encoding="utf-8")
    else:
        print(generated, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
