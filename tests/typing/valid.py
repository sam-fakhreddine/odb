"""Positive static consumer; also checked against the installed wheel."""

from typing import Literal, assert_type

from aws_emulator_shim import (
    Account,
    EvidenceRecord,
    EvidenceSummary,
    Manifest,
    Route,
    aggregate_evidence,
    parse_evidence_record,
    parse_manifest,
)

account = Account(account_id="111111111111", port=9297)
manifest = Manifest(region="us-east-1", accounts={"app": account})
route = Route(source="app", target="app")

assert_type(manifest.accounts["app"], Account)
assert_type(manifest.accounts["app"].port, int)
assert_type(manifest.accounts["app"].account_id, str)
assert_type(parse_manifest(manifest), Manifest)

record = parse_evidence_record({
    "run_id": "run-1", "check_id": "check-1", "operation": "s3:PutObject",
    "outcome": "passed", "provenance": "native", "aws_validation": "confirmed",
})
assert_type(record, EvidenceRecord)
assert_type(record.outcome, Literal["passed", "failed", "not_tested"])
assert_type(aggregate_evidence([record], required_check_ids={"check-1"}), EvidenceSummary)
assert_type(aggregate_evidence([record], required_check_ids={"check-1"}).native_verified, bool)
