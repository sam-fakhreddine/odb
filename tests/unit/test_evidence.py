import copy
import json
import unittest
from pathlib import Path

from aws_emulator_shim.evidence import (
    EvidenceError,
    aggregate_evidence,
    evidence_json_schema,
    parse_evidence_record,
)

ROOT = Path(__file__).resolve().parents[2]
RECORD = {
    "schema_version": 1,
    "run_id": "run-1",
    "check_id": "check-native-pass",
    "operation": "s3:PutObject",
    "outcome": "passed",
    "provenance": "native",
    "assertion": "not_tested",
    "aws_validation": "confirmed",
    "write_state": "not_applicable",
    "fault_id": None,
    "fixture_id": None,
}
ALLOWED_KEYS = set(RECORD)


class EvidenceContractTest(unittest.TestCase):
    def test_record_roundtrips_and_keeps_outcome_provenance_aws_independent(self):
        """Catches: conflating operation outcome, native/adapted provenance or AWS state."""
        record = parse_evidence_record(RECORD)
        self.assertIsNotNone(record)
        self.assertEqual(
            {field: getattr(record, field) for field in ALLOWED_KEYS},
            {
                "schema_version": 1, "run_id": "run-1", "check_id": "check-native-pass",
                "operation": "s3:PutObject", "outcome": "passed", "provenance": "native",
                "assertion": "not_tested", "aws_validation": "confirmed",
                "write_state": "not_applicable", "fault_id": None, "fixture_id": None,
            },
        )
        dumped = record.model_dump(mode="json")
        self.assertEqual(parse_evidence_record(dumped), record)
        self.assertEqual(json.loads(record.model_dump_json()), dumped)
        # Outcome, provenance and AWS validation vary independently: no field
        # implies another, so the same triple roundtrips unchanged.
        combos = (
            ("passed", "native", "not_checked"),
            ("passed", "adapted", "confirmed"),
            ("failed", "unknown", "unconfirmed"),
            ("not_tested", "adapted", "not_checked"),
        )
        for outcome, provenance, aws_validation in combos:
            data = copy.deepcopy(RECORD)
            data.update(outcome=outcome, provenance=provenance, aws_validation=aws_validation)
            parsed = parse_evidence_record(data)
            with self.subTest(outcome=outcome, provenance=provenance, aws_validation=aws_validation):
                self.assertEqual(
                    (parsed.outcome, parsed.provenance, parsed.aws_validation),
                    (outcome, provenance, aws_validation),
                )
        from jsonschema import Draft202012Validator

        schema = json.loads((ROOT / "docs/schemas/evidence-v1.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate(RECORD)
        validator.validate(json.loads((ROOT / "docs/schemas/evidence-v1.example.json").read_text()))
        self.assertEqual(schema, evidence_json_schema())
        for field, value in (
            ("outcome", "success"), ("provenance", "real"), ("aws_validation", "verified"),
            ("schema_version", 2), ("outcome", True), ("provenance", None),
        ):
            data = copy.deepcopy(RECORD)
            data[field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(validator.is_valid(data))
                with self.assertRaises(EvidenceError):
                    parse_evidence_record(data)

    def test_aggregation_requires_unique_checks_and_never_calls_adapted_native(self):
        """Catches: missing/duplicate check IDs and adapted/unknown folded into native passes."""
        native = dict(RECORD, check_id="check-a", provenance="native")
        adapted = dict(RECORD, check_id="check-b", outcome="passed", provenance="adapted")
        summary = aggregate_evidence(
            [parse_evidence_record(native), parse_evidence_record(adapted)],
            required_check_ids={"check-a", "check-b"},
        )
        self.assertIsNotNone(summary)
        self.assertEqual(summary.native_passed, 1)
        self.assertEqual(summary.adapted_passed, 1)
        self.assertEqual(summary.unknown_passed, 0)
        self.assertFalse(summary.native_verified)
        for case, records, required in (
            ("duplicate", [native, dict(native, check_id="check-a")], {"check-a"}),
            ("missing", [native], {"check-a", "check-b"}),
        ):
            with self.subTest(case=case):
                parsed = [parse_evidence_record(item) for item in records]
                with self.assertRaises(EvidenceError):
                    aggregate_evidence(parsed, required_check_ids=required)
        unknown = dict(RECORD, check_id="check-c", provenance="unknown")
        adapted_only = aggregate_evidence(
            [parse_evidence_record(unknown)], required_check_ids={"check-c"},
        )
        self.assertEqual(adapted_only.unknown_passed, 1)
        self.assertFalse(adapted_only.native_verified)

    def test_failed_negative_control_and_unconfirmed_write_stay_unverified(self):
        """Catches: an assertion pass claiming operation success or an unconfirmed write as done."""
        failed_op = dict(
            RECORD, check_id="check-neg", outcome="failed", assertion="passed",
        )
        passed_op = dict(RECORD, check_id="check-pos")
        summary = aggregate_evidence(
            [parse_evidence_record(failed_op), parse_evidence_record(passed_op)],
            required_check_ids={"check-neg", "check-pos"},
        )
        self.assertIsNotNone(summary)
        self.assertEqual(summary.failed, 1)
        self.assertEqual(summary.native_passed, 1)
        self.assertFalse(summary.native_verified)
        unconfirmed = dict(RECORD, check_id="check-write", write_state="unconfirmed")
        write_summary = aggregate_evidence(
            [parse_evidence_record(unconfirmed)], required_check_ids={"check-write"},
        )
        self.assertEqual(write_summary.uncertain_writes, 1)
        self.assertEqual(write_summary.confirmed_writes, 0)
        self.assertFalse(write_summary.native_verified)
        all_native = aggregate_evidence(
            [parse_evidence_record(dict(RECORD, check_id="check-1")),
             parse_evidence_record(dict(RECORD, check_id="check-2"))],
            required_check_ids={"check-1", "check-2"},
        )
        self.assertEqual(all_native.native_passed, 2)
        self.assertTrue(all_native.native_verified)

    def test_serialization_allowlists_metadata_and_rejects_secrets_without_disclosure(self):
        """Catches (non-disclosure): leaked credentials, arbitrary payloads or unsafe diagnostics."""
        record = parse_evidence_record(RECORD)
        self.assertIsNotNone(record)
        self.assertEqual(set(record.model_dump(mode="json")), ALLOWED_KEYS)
        self.assertEqual(set(json.loads(record.model_dump_json())), ALLOWED_KEYS)
        for field, value in (
            ("credentials", "rejected-value-marker"),
            ("access_key_id", "rejected-value-marker"),
            ("token", "rejected-value-marker"),
            ("payload", {"body": "rejected-value-marker"}),
            ("diagnostics", "rejected-value-marker"),
            ("stdout", "rejected-value-marker"),
        ):
            data = dict(RECORD, **{field: value})
            with self.subTest(field=field):
                with self.assertRaises(EvidenceError) as raised:
                    parse_evidence_record(data)
                self.assertNotIn("rejected-value-marker", str(raised.exception))
                self.assertNotIn("rejected-value-marker", repr(raised.exception))


if __name__ == "__main__":
    unittest.main()
