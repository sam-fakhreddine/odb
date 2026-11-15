import argparse
import json

from .harness import Harness


def main():
    parser = argparse.ArgumentParser(
        description="Probe independent local AWS Emulator accounts; not AWS authorization."
    )
    parser.add_argument("manifest", help="JSON account inventory")
    parser.add_argument("--image", help="Existing local image; never pulled automatically")
    parser.add_argument("--engine", choices=("podman", "docker"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--strict-manifest", action="store_true", help="Validate the strict typed inventory contract")
    args = parser.parse_args()
    accounts = {}
    with Harness(
        args.manifest, seed=args.seed, image=args.image, engine=args.engine,
        strict_manifest=args.strict_manifest,
    ) as harness:
        prefix = harness.manifest.get("namespace", "emulator-shim")
        for name in harness.accounts:
            identity = harness.client(name, "sts").get_caller_identity()
            if identity["Account"] != "000000000000":
                raise AssertionError("Unexpected native emulator account")
            marker = f"{name}:native-roundtrip"
            s3 = harness.client(name, "s3")
            bucket = f"{prefix}-smoke"
            region = harness.manifest["region"]
            options = (
                {"CreateBucketConfiguration": {"LocationConstraint": region}}
                if region != "us-east-1" else {}
            )
            s3.create_bucket(Bucket=bucket, **options)
            s3.put_object(Bucket=bucket, Key="marker", Body=marker.encode())
            with s3.get_object(Bucket=bucket, Key="marker")["Body"] as body:
                if body.read() != marker.encode():
                    raise AssertionError("Native S3 bytes do not match")
            queue = harness.create_queue(name, f"{prefix}-smoke")
            sqs = harness.client(name, "sqs")
            sqs.send_message(QueueUrl=queue, MessageBody=marker)
            message = sqs.receive_message(QueueUrl=queue)["Messages"][0]
            if message["Body"] != marker:
                raise AssertionError("Native SQS receipt does not match")
            sqs.delete_message(QueueUrl=queue, ReceiptHandle=message["ReceiptHandle"])
            accounts[name] = {
                "logical_id": harness.logical_id(name),
                "native_id": identity["Account"],
                "marker": marker,
            }
    print(json.dumps({
        "status": "PASS",
        "accounts": accounts,
        "cross_account_security_proven": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
