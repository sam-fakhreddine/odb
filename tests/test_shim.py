import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from botocore.awsrequest import AWSRequest
from botocore.exceptions import EndpointConnectionError, ReadTimeoutError

from aws_emulator_shim import Emulator, Harness

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "examples" / "accounts.json"


class ShimTest(unittest.TestCase):
    def test_inventory_and_routes_reject_invalid_dispatch(self):
        # Catches: invalid inventory or undeclared routes reaching a backend.
        original = json.loads(MANIFEST.read_text())
        for field, value in (("account_id", "222222222222"), ("port", 65536)):
            manifest = copy.deepcopy(original)
            manifest["accounts"]["app"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                Harness(manifest, seed=7)
        harness = Harness(original, seed=7)
        with self.assertRaises(PermissionError):
            harness.assume_role("audit", "SecurityAccess")
        with self.assertRaises(PermissionError):
            harness.assume_role("security", "undeclared")
        with self.assertRaises(ValueError):
            harness.client("undeclared", "s3")
        with self.assertRaises(PermissionError):
            harness.transfer("source", "capture", "target", "copy")
        emulator = Emulator("app", 9297, image=os.environ["AWS_EMULATOR_IMAGE"])
        for url in (
            "https://sts.us-east-1.amazonaws.com/",
            "http://127.0.0.1:9297/",
            "https://127.0.0.1:9298/",
            "https://user@127.0.0.1:9297/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                emulator.guard_request(AWSRequest(method="GET", url=url).prepare())

    def test_native_state_is_independent_of_logical_names(self):
        # Catches: interleaved accounts sharing state, credentials or identity.
        with Harness(MANIFEST, seed=7) as harness:
            for name in ("app", "security", "audit"):
                client = harness.client(name, "s3")
                client.create_bucket(Bucket="same-name")
                client.put_object(Bucket="same-name", Key="marker", Body=name.encode())
            for name in ("audit", "app", "security", "app"):
                with harness.client(name, "s3").get_object(
                    Bucket="same-name", Key="marker"
                )["Body"] as body:
                    self.assertEqual(body.read(), name.encode())
                self.assertEqual(
                    harness.client(name, "sts").get_caller_identity()["Account"],
                    "000000000000",
                )
            target = harness.assume_role("security", "SecurityAccess")
            self.assertEqual(target.account, "app")
            self.assertEqual(harness.logical_id(target.account), "111111111111")

    def test_event_relay_preserves_origin_and_received_payload(self):
        # Catches: the explicit event bridge changing payload or destination.
        with Harness(MANIFEST, seed=7, clock=lambda: 123.0) as harness:
            queue = harness.create_queue("security", "audit-receipts")
            sent = harness.relay_event("audit", {"case": "literal-case"}, queue)
            sqs = harness.client("security", "sqs")
            received = sqs.receive_message(QueueUrl=queue)["Messages"][0]
            envelope = json.loads(received["Body"])
            self.assertEqual(envelope, sent)
            self.assertEqual(envelope["origin"], "333333333333")
            self.assertEqual(envelope["destination"], "222222222222")
            self.assertEqual(envelope["payload"], {"case": "literal-case"})
            self.assertEqual(envelope["time"], 123.0)
            sqs.delete_message(QueueUrl=queue, ReceiptHandle=received["ReceiptHandle"])
            self.assertNotIn("Messages", sqs.receive_message(QueueUrl=queue))

    def test_transfer_preserves_evidence_after_grant_revocation(self):
        # Catches: a copy reporting completion without matching retained bytes.
        with Harness(MANIFEST, seed=7) as harness:
            source = harness.client("app", "s3")
            target = harness.client("security", "s3")
            source.create_bucket(Bucket="source-evidence")
            target.create_bucket(Bucket="target-evidence")
            source.put_object(
                Bucket="source-evidence", Key="capture", Body=b"literal-evidence"
            )
            grant = ("source-evidence", "capture", "target-evidence", "copy")
            harness.grant_transfer(*grant)
            receipt = harness.transfer(*grant)
            self.assertEqual(receipt["source_account"], "111111111111")
            self.assertEqual(receipt["target_account"], "222222222222")
            self.assertEqual(receipt["status"], "completed")
            harness.revoke_transfer(*grant)
            with target.get_object(Bucket="target-evidence", Key="copy")["Body"] as body:
                self.assertEqual(body.read(), b"literal-evidence")
            self.assertNotIn(grant, harness.grants)

    def test_outage_and_lost_response_do_not_report_completion(self):
        # Catches: uncertain or failed native writes becoming successful copies.
        for fault in ("offline", "lost-response"):
            with self.subTest(fault=fault), Harness(MANIFEST, seed=7) as harness:
                source = harness.client("app", "s3")
                target = harness.client("security", "s3")
                source.create_bucket(Bucket="fault-source")
                target.create_bucket(Bucket="fault-target")
                source.put_object(
                    Bucket="fault-source", Key="capture", Body=b"fault-literal"
                )
                harness.grant_transfer("fault-source", "capture", "fault-target", "copy")
                if fault == "offline":
                    harness.emulators["security"].stop_backend()
                    expected = EndpointConnectionError
                else:
                    def lose_response(endpoint_url=target.meta.endpoint_url, **kwargs):
                        raise ReadTimeoutError(endpoint_url=endpoint_url)
                    target.meta.events.register("after-call.s3.PutObject", lose_response)
                    expected = ReadTimeoutError
                with self.assertRaises(expected):
                    harness.transfer("fault-source", "capture", "fault-target", "copy")
                self.assertEqual(harness.trace[-1]["status"], "attempted")
                if fault == "lost-response":
                    target.meta.events.unregister("after-call.s3.PutObject", lose_response)
                    with target.get_object(
                        Bucket="fault-target", Key="copy"
                    )["Body"] as body:
                        self.assertEqual(body.read(), b"fault-literal")

    def test_cli_runs_outside_project_with_two_renamed_accounts(self):
        # Catches: project paths, ambient AWS profiles or a fixed three-account schema.
        manifest = {
            "region": "us-west-2",
            "namespace": "reusable-shim",
            "accounts": {
                "service": {"account_id": "555555555555", "port": 9297},
                "collector": {"account_id": "666666666666", "port": 9298},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps(manifest))
            result = subprocess.run(
                [sys.executable, "-m", "aws_emulator_shim", str(path)],
                cwd=directory,
                env={
                    **os.environ,
                    "PYTHONPATH": str(ROOT),
                    "AWS_PROFILE": "shim-nonexistent-profile",
                    "AWS_CONFIG_FILE": str(Path(directory) / "no-config"),
                    "AWS_SHARED_CREDENTIALS_FILE": str(Path(directory) / "no-credentials"),
                },
                check=True, capture_output=True, text=True, timeout=120,
            )
            report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(set(report["accounts"]), {"service", "collector"})
        self.assertEqual(report["accounts"]["service"], {
            "logical_id": "555555555555",
            "native_id": "000000000000",
            "marker": "service:native-roundtrip",
        })
        self.assertEqual(report["accounts"]["collector"]["logical_id"], "666666666666")
        self.assertFalse(report["cross_account_security_proven"])
