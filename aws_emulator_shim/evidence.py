"""Strict, offline evidence contract; no execution, network or AWS calls.

A record is a caller-supplied claim. It never proves that an operation ran:
provenance labels where the observation came from, the independent AWS
validation state labels whether real AWS confirmed it, and the outcome labels
only the operation. Aggregation keeps these axes apart so adapted or unknown
observations can never be reported as a native, AWS-verified pass.
"""

from collections.abc import Iterable, Sequence
from typing import Annotated, Literal

from pydantic import (
    StringConstraints,
    ValidationError,
    field_validator,
)
from pydantic_core import PydanticCustomError

from .contracts import StrictContract

# Single-token identifiers and operation labels: allowlisted shape, never free
# text, so serialized metadata cannot smuggle secrets or arbitrary payloads.
Token = Annotated[
    str,
    StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]

Outcome = Literal["passed", "failed", "not_tested"]
Provenance = Literal["native", "adapted", "unknown"]
AwsValidation = Literal["not_checked", "confirmed", "unconfirmed"]
WriteState = Literal["not_applicable", "confirmed", "unconfirmed"]


class EvidenceRecord(StrictContract):
    """One caller-supplied observation; fields are independent and untrusted."""

    schema_version: Literal[1] = 1
    run_id: Token
    check_id: Token
    operation: Token
    outcome: Outcome
    provenance: Provenance
    assertion: Outcome = "not_tested"
    aws_validation: AwsValidation = "not_checked"
    write_state: WriteState = "not_applicable"
    fault_id: Token | None = None
    fixture_id: Token | None = None

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version_type(cls, value: object) -> object:
        if type(value) is not int:
            raise PydanticCustomError("schema_version_type", "Schema version must be an integer")
        return value


class EvidenceIssue:
    __slots__ = ("code", "path")

    def __init__(self, path: tuple[str | int, ...], code: str) -> None:
        self.path = path
        self.code = code


class EvidenceError(ValueError):
    """Public diagnostic contains only allowlisted field paths and error codes."""

    def __init__(self, issues: tuple[EvidenceIssue, ...]) -> None:
        self.issues = issues
        details = "; ".join(
            f"{'.'.join(map(str, issue.path)) or 'evidence'} [{issue.code}]"
            for issue in issues
        )
        super().__init__(f"Invalid evidence: {details}")


def parse_evidence_record(data: object) -> EvidenceRecord:
    """Validate one unknown record without coercion or value disclosure."""
    try:
        return EvidenceRecord.model_validate(data)
    except ValidationError as error:
        fields = {
            "schema_version", "run_id", "check_id", "operation", "outcome",
            "provenance", "assertion", "aws_validation", "write_state",
            "fault_id", "fixture_id",
        }
        issues = tuple(
            EvidenceIssue(
                tuple(part if part in fields else "*" for part in item["loc"]),
                item["type"],
            )
            for item in error.errors(include_url=False, include_context=False, include_input=False)
        )
        raise EvidenceError(issues) from None


class EvidenceSummary(StrictContract):
    """Derived counts. native_verified is only true for AWS-confirmed native passes."""

    schema_version: Literal[1] = 1
    run_id: Token
    native_passed: int
    adapted_passed: int
    unknown_passed: int
    failed: int
    not_tested: int
    confirmed_writes: int
    uncertain_writes: int
    native_verified: bool


def aggregate_evidence(
    records: Sequence[EvidenceRecord],
    *,
    required_check_ids: Iterable[str],
) -> EvidenceSummary:
    """Aggregate complete, uniquely identified checks; never promote non-native passes."""
    required = set(required_check_ids)
    if not required:
        raise EvidenceError((EvidenceIssue((), "empty_required_checks"),))
    seen: set[str] = set()
    run_ids = {record.run_id for record in records}
    if len(run_ids) != 1:
        raise EvidenceError((EvidenceIssue((), "mixed_run_id"),))
    counts = {
        "native_passed": 0, "adapted_passed": 0, "unknown_passed": 0,
        "failed": 0, "not_tested": 0, "confirmed_writes": 0, "uncertain_writes": 0,
    }
    for record in records:
        if record.check_id in seen:
            raise EvidenceError((EvidenceIssue(("check_id",), "duplicate_check_id"),))
        seen.add(record.check_id)
        if record.outcome == "failed":
            counts["failed"] += 1
        elif record.outcome == "not_tested":
            counts["not_tested"] += 1
        elif record.provenance == "native":
            counts["native_passed"] += 1
        elif record.provenance == "adapted":
            counts["adapted_passed"] += 1
        else:
            counts["unknown_passed"] += 1
        if record.write_state == "confirmed":
            counts["confirmed_writes"] += 1
        elif record.write_state == "unconfirmed":
            counts["uncertain_writes"] += 1
    missing = required - seen
    if missing:
        raise EvidenceError((EvidenceIssue(("check_id",), "missing_required_check"),))
    native_verified = bool(records) and (
        counts["failed"] == 0
        and counts["not_tested"] == 0
        and counts["adapted_passed"] == 0
        and counts["unknown_passed"] == 0
        and counts["uncertain_writes"] == 0
        and all(record.aws_validation == "confirmed" for record in records)
    )
    return EvidenceSummary(
        schema_version=1,
        run_id=next(iter(run_ids)),
        native_passed=counts["native_passed"],
        adapted_passed=counts["adapted_passed"],
        unknown_passed=counts["unknown_passed"],
        failed=counts["failed"],
        not_tested=counts["not_tested"],
        confirmed_writes=counts["confirmed_writes"],
        uncertain_writes=counts["uncertain_writes"],
        native_verified=native_verified,
    )


def evidence_json_schema() -> dict[str, object]:
    schema: dict[str, object] = EvidenceRecord.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:odb:evidence:1"
    schema["$comment"] = (
        "Structural validation only. A record is a caller-supplied claim, not "
        "proof of execution; use aggregate_evidence for unique/complete checks "
        "and the independent native/adapted/unknown and AWS-confirmed rules."
    )
    return schema
