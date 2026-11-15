"""Offline evidence contract (seam 1 RED entry points; no execution or AWS calls)."""


class EvidenceError(ValueError):
    """A rejected evidence record or aggregation; never treat invalid input as a pass."""


def parse_evidence_record(data):
    return None


def aggregate_evidence(records, *, required_check_ids):
    return None


def evidence_json_schema():
    return {}
