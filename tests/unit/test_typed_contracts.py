import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aws_emulator_shim import Harness
from aws_emulator_shim.__main__ import main
from aws_emulator_shim.contracts import ManifestError, load_manifest, parse_manifest

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = {
    "region": "us-east-1",
    "accounts": {
        "caller": {"account_id": "111111111111", "port": 9297},
        "target": {"account_id": "222222222222", "port": 9298},
    },
    "roles": {"Access": {"source": "caller", "target": "target"}},
    "bridges": {"events": {"source": "caller", "target": "target"}},
}


class TypedContractTest(unittest.TestCase):
    def test_examples_roundtrip_and_structural_schema_matches_models(self):
        """Catches: hand-written schema drift, lost fields and untyped snapshots."""
        self.assertIsNotNone(parse_manifest(INVENTORY))
        for path in ("examples/accounts.json", "examples/three_tier/accounts.json"):
            with self.subTest(path=path):
                manifest = parse_manifest(json.loads((ROOT / path).read_text()))
                self.assertIsNotNone(manifest)
                self.assertIsInstance(manifest.accounts["web" if "three_tier" in path else "app"].port, int)
                serialized = manifest.model_dump(mode="json")
                self.assertEqual(parse_manifest(serialized), manifest)
                self.assertEqual(json.loads(manifest.model_dump_json()), serialized)
        from jsonschema import Draft202012Validator

        schema = json.loads((ROOT / "docs/schemas/manifest-v1.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate(INVENTORY)
        for field, value in (("port", True), ("port", "9297"), ("account_id", 111111111111)):
            data = copy.deepcopy(INVENTORY)
            data["accounts"]["caller"][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(validator.is_valid(data))

    def test_wrong_types_extra_fields_and_invalid_relationships_fail(self):
        """Catches: coercion, ignored fields and ambiguous/undeclared routes."""
        rows = (
            (("accounts", "caller", "port"), True),
            (("accounts", "caller", "port"), "9297"),
            (("accounts", "caller", "port"), 9297.0),
            (("accounts", "caller", "port"), 1023),
            (("accounts", "caller", "port"), 65536),
            (("accounts", "caller", "port"), 9298),
            (("accounts", "caller", "account_id"), 111111111111),
            (("accounts", "caller", "account_id"), "000000000000"),
            (("accounts", "caller", "account_id"), "222222222222"),
            (("accounts", "caller", "account_id"), "11111111111x"),
            (("accounts", "caller", "unknown"), "rejected-value-marker"),
            (("roles", "Access", "target"), "absent"),
            (("roles", "Access", "unknown"), "rejected-value-marker"),
            (("bridges", "events", "target"), "caller"),
            (("bridges", "unknown"), {"source": "caller", "target": "target"}),
            (("region",), " "),
            (("namespace",), "trailing-"),
            (("namespace",), "a" * 37),
            (("engine",), "shell"),
            (("image",), "-option"),
            (("accounts",), {}),
            (("region",), None),
            (("schema_version",), 2),
            (("unknown",), "rejected-value-marker"),
        )
        for path, value in rows:
            data = copy.deepcopy(INVENTORY)
            target = data
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path, value=value):
                with self.assertRaises(ManifestError) as raised:
                    parse_manifest(data)
                self.assertNotIn("rejected-value-marker", str(raised.exception))
                self.assertTrue(raised.exception.issues)

    def test_snapshot_and_safe_json_loader_reject_mutation_and_input_disclosure(self):
        """Catches: shallow freezing, last-key-wins JSON and rejected-value disclosure."""
        data = copy.deepcopy(INVENTORY)
        manifest = parse_manifest(data)
        self.assertIsNotNone(manifest)
        data["accounts"]["caller"]["port"] = 9298
        self.assertEqual(manifest.accounts["caller"].port, 9297)
        for mapping in (manifest.accounts, manifest.roles, manifest.bridges):
            with self.assertRaises(TypeError):
                mapping["injected"] = None
        with self.assertRaises(ValueError):
            manifest.accounts["caller"].port = 9298
        with self.assertRaises(ValueError):
            manifest.region = "us-west-2"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(INVENTORY))
            self.assertEqual(load_manifest(path), manifest)
            for raw in (
                '{"region": "a", "region": "rejected-value-marker"}',
                '{"accounts": {"x": {"port": 9297, "port": 9298}}}',
                '{"region": NaN}',
                '{"region": Infinity}',
                '{"region": -Infinity}',
                '{"region": "rejected-value-marker"',
                '["rejected-value-marker"]',
                '{"rejected-value-marker": "rejected-value-marker"}',
            ):
                path.write_text(raw)
                with self.subTest(raw=raw):
                    with self.assertRaises(ManifestError) as raised:
                        load_manifest(path)
                    self.assertNotIn("rejected-value-marker", str(raised.exception))
                    self.assertNotIn("rejected-value-marker", repr(raised.exception.issues))

    def test_strict_harness_and_cli_are_opt_in_before_startup(self):
        """Catches: implicit strict-mode activation or runtime startup on invalid input."""
        self.assertIn("strict_manifest", inspect.signature(Harness).parameters)
        data = copy.deepcopy(INVENTORY)
        data["unknown"] = "rejected-value-marker"
        with patch("aws_emulator_shim.harness.Emulator") as emulator:
            legacy = Harness(data, seed=7, image="local-test")
            self.assertEqual(legacy.manifest["unknown"], "rejected-value-marker")
            with self.assertRaises(ManifestError):
                Harness(data, seed=7, image="local-test", strict_manifest=True)
            strict = Harness(INVENTORY, seed=7, image="local-test", strict_manifest=True)
            self.assertEqual(strict.inventory, parse_manifest(INVENTORY))
            self.assertEqual(strict.logical_id("caller"), "111111111111")
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(INVENTORY))
                self.assertEqual(
                    Harness(path, seed=7, image="local-test", strict_manifest=True).inventory,
                    strict.inventory,
                )
                path.write_text(json.dumps(data))
                with patch("sys.argv", ["odb", str(path), "--strict-manifest", "--image", "local-test"]):
                    with self.assertRaises(ManifestError):
                        main()
            emulator.assert_not_called()
        for options, enabled in (([], False), (["--strict-manifest"], True)):
            with patch("sys.argv", ["odb", "inventory.json", *options]):
                with patch("aws_emulator_shim.__main__.Harness") as harness:
                    harness.return_value.__enter__.return_value.accounts = ()
                    with patch("builtins.print"):
                        main()
                    self.assertIs(harness.call_args.kwargs["strict_manifest"], enabled)


if __name__ == "__main__":
    unittest.main()
