import unittest

from examples.three_tier.demo import HERE, run


class ThreeTierTest(unittest.TestCase):
    def test_native_components_explicit_relays_and_broken_plumbing(self):
        report = run(HERE / "accounts.json")
        self.assertEqual(report["status"], "PASS_ADAPTED")
        results = report["checks"]["http_native_business_results"]
        self.assertNotEqual(results[0]["total_cents"], results[1]["total_cents"])
        self.assertNotEqual(results[0]["request_id"], results[1]["request_id"])
        self.assertEqual(len(report["receipts"]), 4)
        self.assertEqual(
            report["checks"]["stopped_native_business_backend"]["exception"],
            "EndpointConnectionError",
        )
        self.assertFalse(report["native_cross_account_proven"])
