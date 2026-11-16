"""Offline property tests over trust-boundary contracts; no network or AWS.

Hypothesis runs with derandomized seeds and no example database so each run is
reproducible. Properties name the security-relevant domain per TDD-008.
"""

import copy
import unittest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from aws_emulator_shim.contracts import ManifestError, parse_manifest

SECRET = "zz-rejected-value-marker"
TOP_LEVEL = {"schema_version", "region", "namespace", "accounts", "roles", "bridges", "image", "engine"}
LOGICAL_ID = st.from_regex(r"[1-9][0-9]{11}", fullmatch=True)
VALID_PORT = st.integers(min_value=1024, max_value=65535)
REGION = st.from_regex(r"[A-Za-z0-9][A-Za-z0-9-]{0,15}", fullmatch=True)


def manifest_dict(region, app_id, app_port, web_id, web_port):
    return {
        "region": region,
        "accounts": {
            "app": {"account_id": app_id, "port": app_port},
            "web": {"account_id": web_id, "port": web_port},
        },
        "roles": {},
        "bridges": {"events": {"source": "app", "target": "web"}},
    }


class ContractPropertyTest(unittest.TestCase):
    @settings(max_examples=50, deadline=None, derandomize=True, database=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(port=st.one_of(st.booleans(), st.integers(max_value=1023), st.integers(min_value=65536)))
    def test_out_of_range_or_nonint_port_is_never_accepted(self, port):
        """Catches (Integrity): coerced booleans or out-of-range ports reaching a manifest."""
        data = manifest_dict("us-east-1", "111111111111", 9297, "222222222222", 9298)
        data["accounts"]["app"]["port"] = port
        with self.assertRaises(ManifestError):
            parse_manifest(data)

    @settings(max_examples=50, deadline=None, derandomize=True, database=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(key=st.text(min_size=1, max_size=24).filter(lambda value: value not in TOP_LEVEL))
    def test_rejected_extra_values_are_never_disclosed(self, key):
        """Catches (SAFETY/non-disclosure): a leaked rejected value in a parse diagnostic."""
        data = manifest_dict("us-east-1", "111111111111", 9297, "222222222222", 9298)
        data[key] = SECRET
        with self.assertRaises(ManifestError) as raised:
            parse_manifest(data)
        self.assertNotIn(SECRET, str(raised.exception))
        self.assertNotIn(SECRET, repr(raised.exception.issues))

    @settings(max_examples=50, deadline=None, derandomize=True, database=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(region=REGION, app_id=LOGICAL_ID, app_port=VALID_PORT, web_id=LOGICAL_ID, web_port=VALID_PORT)
    def test_valid_manifest_roundtrips_and_shrugs_off_source_mutation(self, region, app_id, app_port, web_id, web_port):
        """Catches (Integrity): shallow freezing or lost fields across a serialized round-trip."""
        if app_id == web_id or app_port == web_port:
            return
        data = manifest_dict(region, app_id, app_port, web_id, web_port)
        manifest = parse_manifest(data)
        dumped = manifest.model_dump(mode="json")
        self.assertEqual(parse_manifest(dumped), manifest)
        mutated = copy.deepcopy(data)
        mutated["accounts"]["app"]["port"] = 41000
        mutated["accounts"].pop("web")
        self.assertEqual(manifest.accounts["app"].port, app_port)
        self.assertEqual(set(manifest.accounts), {"app", "web"})

    @settings(max_examples=50, deadline=None, derandomize=True, database=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(target=st.sampled_from(["app", "ghost", "web2", "", "web "]))
    def test_bridge_to_self_or_undeclared_account_is_never_accepted(self, target):
        """Catches (Integrity): a bridge silently pointing at itself or an undeclared account."""
        data = manifest_dict("us-east-1", "111111111111", 9297, "222222222222", 9298)
        data["bridges"]["events"]["target"] = target
        with self.assertRaises(ManifestError):
            parse_manifest(data)


if __name__ == "__main__":
    unittest.main()
