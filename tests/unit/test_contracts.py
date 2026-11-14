import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.awsrequest import AWSRequest

from aws_emulator_shim import Emulator, Harness
from aws_emulator_shim.runtime import local_session

MANIFEST = {
    "region": "us-east-1",
    "accounts": {
        "caller": {"account_id": "111111111111", "port": 9297},
        "target": {"account_id": "222222222222", "port": 9298},
    },
    "roles": {"TestRoute": {"source": "caller", "target": "target"}},
}


class ContractTest(unittest.TestCase):
    def harness(self, manifest=None):
        return Harness(MANIFEST if manifest is None else manifest, seed=7, image="local-test")

    def test_inventory_cannot_be_changed_by_mutating_caller_input(self):
        manifest = copy.deepcopy(MANIFEST)
        harness = self.harness(manifest)
        manifest["accounts"]["caller"]["account_id"] = "999999999999"
        manifest["roles"]["TestRoute"]["target"] = "caller"
        self.assertEqual(harness.logical_id("caller"), "111111111111")
        self.assertEqual(harness.roles["TestRoute"]["target"], "target")

    def test_ambiguous_or_invalid_account_identities_and_ports_are_rejected(self):
        for field, values in (
            ("account_id", ("222222222222", "000000000000", "not-an-account", 111111111111)),
            ("port", (9298, True, 1023, 65536, "9297")),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    manifest = copy.deepcopy(MANIFEST)
                    manifest["accounts"]["caller"][field] = value
                    with self.assertRaises(ValueError):
                        self.harness(manifest)

    def test_invalid_or_same_account_bridge_is_rejected(self):
        for target in ("absent", "caller"):
            manifest = copy.deepcopy(MANIFEST)
            manifest["bridges"] = {"events": {"source": "caller", "target": target}}
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.harness(manifest)

    def test_unknown_roles_and_wrong_callers_cannot_select_a_backend(self):
        harness = self.harness()
        harness.emulators["target"] = object()
        for caller, role in (("caller", "absent"), ("target", "TestRoute")):
            with self.subTest(caller=caller), self.assertRaises(PermissionError):
                harness.assume_role(caller, role)
        self.assertIs(harness.assume_role("caller", "TestRoute"), harness.emulators["target"])

    def test_unstarted_target_and_unknown_accounts_fail_explicitly(self):
        harness = self.harness()
        with self.assertRaises(RuntimeError):
            harness.assume_role("caller", "TestRoute")
        with self.assertRaises(RuntimeError):
            harness.client("caller", "sts")
        with self.assertRaises(ValueError):
            harness.client("absent", "sts")

    def test_endpoint_guard_accepts_only_the_declared_tls_loopback_endpoint(self):
        emulator = Emulator("test", 9297, image="local-test")
        emulator.guard_request(AWSRequest(url="https://127.0.0.1:9297/").prepare())
        for url in (
            "https://sts.us-east-1.amazonaws.com/",
            "https://localhost:9297/",
            "http://127.0.0.1:9297/",
            "https://127.0.0.1:9298/",
            "https://user@127.0.0.1:9297/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                emulator.guard_request(AWSRequest(url=url).prepare())

    def test_explicit_session_ignores_nonexistent_ambient_profile_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = {
                "AWS_PROFILE": "odb-profile-does-not-exist",
                "AWS_CONFIG_FILE": str(Path(directory) / "missing-config"),
                "AWS_SHARED_CREDENTIALS_FILE": str(Path(directory) / "missing-credentials"),
            }
            with patch.dict(os.environ, settings):
                session = local_session("local-test-key", "local-test-secret", "us-west-2")
                self.assertEqual(session.region_name, "us-west-2")
                self.assertEqual(session.get_credentials().access_key, "local-test-key")
                for key, value in settings.items():
                    self.assertEqual(os.environ[key], value)

    def test_partial_startup_closes_already_started_runtime(self):
        first, second = MagicMock(), MagicMock()
        first.__enter__.return_value = first
        second.__enter__.side_effect = RuntimeError("local startup failed")
        with patch("aws_emulator_shim.harness.Emulator", side_effect=[first, second]):
            with self.assertRaisesRegex(RuntimeError, "local startup failed"):
                with self.harness():
                    self.fail("A failed startup must not enter the harness")
        first.__exit__.assert_called_once()

    def test_cleanup_keeps_original_error_and_continues_after_client_close_failure(self):
        emulator = Emulator("test", 9297, image="local-test")
        first, second = MagicMock(), MagicMock()
        first.close.side_effect = OSError("close failed")
        emulator.clients = {"one": first, "two": second}
        directory = MagicMock()
        emulator.directory = directory
        original = ValueError("application failed")
        with self.assertRaises(BaseExceptionGroup) as raised:
            emulator.__exit__(ValueError, original, None)
        self.assertIs(raised.exception.exceptions[0], original)
        second.close.assert_called_once()
        directory.cleanup.assert_called_once()
        self.assertIsNone(emulator.session)
        self.assertEqual(emulator.clients, {})

    def test_missing_transfer_grant_does_not_contact_a_client(self):
        harness = self.harness()
        with patch.object(harness, "client") as client:
            with self.assertRaises(PermissionError):
                harness.transfer("source", "key", "target", "key")
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
