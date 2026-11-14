"""Local three-account example; no real AWS endpoints or credentials are used."""

import argparse
import base64
import copy
import hashlib
import io
import json
import subprocess
import sys
import threading
import uuid
import zipfile
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import ProxyHandler, build_opener

from botocore.exceptions import ClientError, EndpointConnectionError

from aws_emulator_shim import Harness

HERE = Path(__file__).resolve().parent
FUNCTION = "odb-quote"
BUCKET = "odb-three-tier-site"


def equal(actual, expected):
    if actual != expected:
        raise AssertionError(f"Expected {expected!r}; observed {actual!r}")


def refused(operation, exception, code=None):
    try:
        operation()
    except exception as error:
        if code is not None:
            equal(error.response["Error"]["Code"], code)
        return {"exception": type(error).__name__, "message": str(error)}
    raise AssertionError("Broken plumbing unexpectedly returned a successful response")


class ThreeTier:
    """Deploy native components and expose only the two named fixture seams."""

    def __init__(self, harness):
        self.harness = harness
        self.subnets = []
        self.receipts = []
        self.s3 = harness.client("web", "s3")
        self.cf = harness.client("web", "cloudfront")
        self.functions = harness.client("application", "lambda")
        self.owner_ec2 = harness.client("network", "ec2")
        self.app_ec2 = harness.client("application", "ec2")
        self.ram = harness.client("network", "ram")

    def deploy(self):
        region = self.harness.manifest["region"]
        owner_vpc = self.owner_ec2.create_vpc(CidrBlock="10.70.0.0/16")["Vpc"]
        self.canary_vpc = self.app_ec2.create_vpc(CidrBlock="10.91.0.0/16")["Vpc"]
        participant_vpc = self.app_ec2.create_vpc(CidrBlock=owner_vpc["CidrBlock"])["Vpc"]
        self.owner_vpc = owner_vpc["VpcId"]
        self.participant_vpc = participant_vpc["VpcId"]
        for number, zone in enumerate((f"{region}a", f"{region}b"), start=1):
            owner = self.owner_ec2.create_subnet(
                VpcId=self.owner_vpc, CidrBlock=f"10.70.{number}.0/24",
                AvailabilityZone=zone,
            )["Subnet"]
            participant = self.app_ec2.create_subnet(
                VpcId=self.participant_vpc, CidrBlock=owner["CidrBlock"],
                AvailabilityZone=owner["AvailabilityZone"],
            )["Subnet"]
            self.subnets.append({
                "owner_id": owner["SubnetId"],
                "owner_arn": owner["SubnetArn"],
                "participant_id": participant["SubnetId"],
                "cidr": owner["CidrBlock"],
                "zone": owner["AvailabilityZone"],
            })
        self.share = self.ram.create_resource_share(
            name="odb-business-subnets",
            resourceArns=[subnet["owner_arn"] for subnet in self.subnets],
            principals=[self.harness.logical_id("application")],
            allowExternalPrincipals=False,
        )["resourceShare"]
        self.security_group = self.app_ec2.create_security_group(
            GroupName="odb-business", Description="Local Lambda subnet fixture",
            VpcId=self.participant_vpc,
        )["GroupId"]
        iam = self.harness.client("application", "iam")
        role = iam.create_role(
            RoleName="odb-business",
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }],
            }),
        )["Role"]["Arn"]
        self.role = role
        self.missing_vpc_permission = refused(
            lambda: self.create_function("odb-without-vpc-permission"),
            self.functions.exceptions.InvalidParameterValueException,
        )
        iam.attach_role_policy(
            RoleName="odb-business",
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
        )
        self.create_function(FUNCTION)
        self.functions.get_waiter("function_active_v2").wait(
            FunctionName=FUNCTION, WaiterConfig={"Delay": 1, "MaxAttempts": 30},
        )
        self.function_url = self.functions.create_function_url_config(
            FunctionName=FUNCTION, AuthType="AWS_IAM",
        )["FunctionUrl"]
        bucket_options = {}
        if region != "us-east-1":
            bucket_options["CreateBucketConfiguration"] = {"LocationConstraint": region}
        self.s3.create_bucket(Bucket=BUCKET, **bucket_options)
        self.site = (HERE / "index.html").read_bytes()
        self.s3.put_object(
            Bucket=BUCKET, Key="index.html", Body=self.site, ContentType="text/html",
        )
        origins = []
        for name, kind in (("site", "s3"), ("business", "lambda")):
            oac = self.cf.create_origin_access_control(OriginAccessControlConfig={
                "Name": f"odb-{name}", "SigningProtocol": "sigv4",
                "SigningBehavior": "always", "OriginAccessControlOriginType": kind,
            })["OriginAccessControl"]["Id"]
            origin = {
                "Id": name, "OriginAccessControlId": oac,
                "DomainName": (
                    f"{BUCKET}.s3.{region}.amazonaws.com" if kind == "s3"
                    else urlsplit(self.function_url).hostname
                ),
            }
            if kind == "s3":
                origin["S3OriginConfig"] = {"OriginAccessIdentity": ""}
            else:
                origin["CustomOriginConfig"] = {
                    "HTTPPort": 80, "HTTPSPort": 443, "OriginProtocolPolicy": "https-only",
                    "OriginSslProtocols": {"Quantity": 1, "Items": ["TLSv1.2"]},
                }
            origins.append(origin)
        self.distribution = self.cf.create_distribution(DistributionConfig={
            "CallerReference": uuid.uuid4().hex, "Comment": "ODB local three-tier fixture",
            "Enabled": True, "DefaultRootObject": "index.html",
            "Origins": {"Quantity": 2, "Items": origins},
            "DefaultCacheBehavior": self.behavior("site", False),
            "CacheBehaviors": {
                "Quantity": 1,
                "Items": [{"PathPattern": "/api/*", **self.behavior("business", True)}],
            },
        })["Distribution"]
        self.bucket_policy = json.dumps({
            "Version": "2012-10-17", "Statement": [{
                "Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"},
                "Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{BUCKET}/*",
                "Condition": {"StringEquals": {"AWS:SourceArn": self.distribution["ARN"]}},
            }],
        })
        self.s3.put_bucket_policy(Bucket=BUCKET, Policy=self.bucket_policy)
        for statement, action in (
            ("cloudfront-url", "lambda:InvokeFunctionUrl"),
            ("cloudfront-invoke", "lambda:InvokeFunction"),
        ):
            permission = {
                "FunctionName": FUNCTION, "StatementId": statement,
                "Principal": "cloudfront.amazonaws.com", "Action": action,
                "SourceArn": self.distribution["ARN"],
            }
            if action == "lambda:InvokeFunctionUrl":
                permission["FunctionUrlAuthType"] = "AWS_IAM"
            self.functions.add_permission(**permission)

    @staticmethod
    def behavior(origin, query):
        return {
            "TargetOriginId": origin, "ViewerProtocolPolicy": "allow-all",
            "ForwardedValues": {"QueryString": query, "Cookies": {"Forward": "none"}},
            "MinTTL": 0, "DefaultTTL": 0, "MaxTTL": 0,
        }

    def create_function(self, name, subnet_ids=None):
        code = io.BytesIO()
        with zipfile.ZipFile(code, "w") as archive:
            archive.write(HERE / "business.py", "business.py")
        self.code = code.getvalue()
        return self.functions.create_function(
            FunctionName=name, Runtime="python3.12", Role=self.role,
            Handler="business.handler", Code={"ZipFile": self.code},
            VpcConfig={
                "SubnetIds": (
                    [subnet["participant_id"] for subnet in self.subnets]
                    if subnet_ids is None else subnet_ids
                ),
                "SecurityGroupIds": [self.security_group],
            },
        )

    def native_edge(self, path, *, account="web", distribution=None):
        if not path.startswith("/") or "\r" in path or "\n" in path:
            raise ValueError("An origin-relative path is required")
        address = urlsplit("http://" + (distribution or self.distribution)["DomainName"])
        if address.hostname != "127.0.0.1" or not address.port or address.path:
            raise ValueError("This example requires a native loopback edge listener")
        emulator = self.harness.emulators[account]
        response = subprocess.run(
            [
                emulator.engine, "exec", emulator.container_id, "curl",
                "--noproxy", "*", "--max-time", "10", "--silent", "--show-error",
                "--include", "--path-as-is", "http://" + address.netloc + path,
            ],
            capture_output=True, check=True, timeout=15,
        ).stdout
        head, body = response.split(b"\r\n\r\n", 1)
        return int(head.split(b" ", 2)[1]), body

    def same_process_origin_control(self):
        cf = self.harness.client("application", "cloudfront")
        oac = cf.create_origin_access_control(OriginAccessControlConfig={
            "Name": "odb-local-control", "SigningProtocol": "sigv4",
            "SigningBehavior": "always", "OriginAccessControlOriginType": "lambda",
        })["OriginAccessControl"]["Id"]
        origin = copy.deepcopy(self.distribution["DistributionConfig"]["Origins"]["Items"][1])
        origin["OriginAccessControlId"] = oac
        distribution = cf.create_distribution(DistributionConfig={
            "CallerReference": uuid.uuid4().hex, "Comment": "Same-process diagnostic only",
            "Enabled": True, "Origins": {"Quantity": 1, "Items": [origin]},
            "DefaultCacheBehavior": self.behavior("business", True),
        })["Distribution"]
        try:
            for name, action in (
                ("local-control-url", "lambda:InvokeFunctionUrl"),
                ("local-control-invoke", "lambda:InvokeFunction"),
            ):
                options = {}
                if action == "lambda:InvokeFunctionUrl":
                    options["FunctionUrlAuthType"] = "AWS_IAM"
                self.functions.add_permission(
                    FunctionName=FUNCTION, StatementId=name,
                    Principal="cloudfront.amazonaws.com", Action=action,
                    SourceArn=distribution["ARN"], **options,
                )
            status, body = self.native_edge(
                "/api/quote?quantity=3&unit_cents=1299&discount_percent=10",
                account="application", distribution=distribution,
            )
            equal(status, 200)
            result = json.loads(body)
            equal(result["total_cents"], 3508)
            return {"http_status": status, "result": result}
        finally:
            current = cf.get_distribution_config(Id=distribution["Id"])
            current["DistributionConfig"]["Enabled"] = False
            updated = cf.update_distribution(
                Id=distribution["Id"], IfMatch=current["ETag"],
                DistributionConfig=current["DistributionConfig"],
            )
            cf.get_waiter("distribution_deployed").wait(
                Id=distribution["Id"], WaiterConfig={"Delay": 1, "MaxAttempts": 60},
            )
            cf.delete_distribution(Id=distribution["Id"], IfMatch=updated["ETag"])

    def validate_shared_fixture(self):
        owner = self.harness.assume_role("application", "SharedNetwork")
        equal(owner.account, "network")
        associations = self.ram.get_resource_share_associations(
            associationType="RESOURCE", resourceShareArns=[self.share["resourceShareArn"]],
        )["resourceShareAssociations"]
        for association in associations:
            if association["status"] not in ("ASSOCIATING", "ASSOCIATED"):
                raise PermissionError("Owner RAM resource declaration was revoked")
        equal(
            {entry["associatedEntity"] for entry in associations},
            {subnet["owner_arn"] for subnet in self.subnets},
        )
        principals = self.ram.get_resource_share_associations(
            associationType="PRINCIPAL", resourceShareArns=[self.share["resourceShareArn"]],
        )["resourceShareAssociations"]
        for principal in principals:
            if principal["status"] not in ("ASSOCIATING", "ASSOCIATED"):
                raise PermissionError("Owner RAM principal declaration was revoked")
        equal(
            {entry["associatedEntity"] for entry in principals},
            {self.harness.logical_id("application")},
        )
        for mapping in self.subnets:
            for client, key, vpc in (
                (owner.client("ec2"), "owner_id", self.owner_vpc),
                (self.app_ec2, "participant_id", self.participant_vpc),
            ):
                subnet = client.describe_subnets(SubnetIds=[mapping[key]])["Subnets"][0]
                equal(subnet["VpcId"], vpc)
                equal(subnet["CidrBlock"], mapping["cidr"])
                equal(subnet["AvailabilityZone"], mapping["zone"])
        configuration = self.functions.get_function_configuration(FunctionName=FUNCTION)
        equal(
            set(configuration["VpcConfig"]["SubnetIds"]),
            {subnet["participant_id"] for subnet in self.subnets},
        )
        equal(configuration["VpcConfig"]["SecurityGroupIds"], [self.security_group])

    def relay(self, path):
        """Replace only cross-process API transport; never synthesize business output."""
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc:
            raise ValueError("Only origin-relative requests are accepted")
        if parsed.path != "/api/quote":
            status, body = self.native_edge(path)
            return status, body, "text/html"
        configuration = self.cf.get_distribution_config(
            Id=self.distribution["Id"],
        )["DistributionConfig"]
        behaviors = configuration["CacheBehaviors"]["Items"]
        equal(
            [(item["PathPattern"], item["TargetOriginId"]) for item in behaviors],
            [("/api/*", "business")],
        )
        origins = {item["Id"]: item for item in configuration["Origins"]["Items"]}
        equal(origins["business"]["DomainName"], urlsplit(self.function_url).hostname)
        target = self.harness.assume_role("web", "BusinessOrigin")
        equal(target.account, "application")
        self.validate_shared_fixture()
        request_id = uuid.uuid4().hex
        response = target.client("lambda").invoke(
            FunctionName=FUNCTION, InvocationType="RequestResponse",
            Payload=json.dumps({
                "version": "2.0", "rawPath": parsed.path,
                "queryStringParameters": {
                    key: values[-1] for key, values in parse_qs(
                        parsed.query, keep_blank_values=True,
                    ).items()
                },
                "requestContext": {"requestId": request_id},
            }).encode(),
        )
        with response["Payload"] as stream:
            payload = stream.read()
        if response.get("FunctionError"):
            raise RuntimeError(f"Native Lambda failed: {payload.decode()}")
        result = json.loads(payload)
        self.receipts.append({
            "simulation": "cross-account-function-url-relay",
            "source": self.harness.logical_id("web"),
            "target": self.harness.logical_id(target.account),
            "path": path, "request_id": request_id,
            "native_lambda_status": response["StatusCode"],
            "function_status": result["statusCode"],
        })
        return result["statusCode"], result["body"].encode(), "application/json"


@contextmanager
def serve(example, port=0):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                status, body, content_type = example.relay(self.path)
            except (
                ClientError, EndpointConnectionError, PermissionError,
                AssertionError, RuntimeError, subprocess.SubprocessError,
            ) as error:
                print(f"Relay refused request: {error}", file=sys.stderr)
                status, body, content_type = 502, b'{"error":"Upstream request failed"}', "application/json"
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, message, *args):
            print(f"HTTP {message % args}", file=sys.stderr)

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}"
        finally:
            server.shutdown()
            thread.join()


def exercise(example):
    report = {
        "scope": "adapted local three-account plumbing, not AWS networking/authorization",
        "native_cross_account_proven": False,
        "accounts": {
            name: {
                "logical_id": example.harness.logical_id(name),
                "native_id": example.harness.client(name, "sts").get_caller_identity()["Account"],
                "endpoint": emulator.endpoint,
            }
            for name, emulator in example.harness.emulators.items()
        },
        "subnet_fixture": {
            "simulation": "owner-to-participant-subnet-mapping; distinct native VPCs",
            "owner_vpc": example.owner_vpc,
            "participant_vpc": example.participant_vpc,
            "subnets": copy.deepcopy(example.subnets),
            "ram_share": example.share["resourceShareArn"],
        },
        "checks": {}, "native_diagnostics": {},
    }
    checks = report["checks"]
    checks["native_execution_role_missing_network_permission"] = example.missing_vpc_permission
    checks["native_same_process_cloudfront_lambda_oac_control"] = example.same_process_origin_control()
    native_status, native_body = example.native_edge("/api/quote?quantity=3&unit_cents=1299")
    native_api_ok = False
    if native_status == 200:
        value = json.loads(native_body)
        native_api_ok = (
            value.get("subtotal_cents") == 3897 and value.get("total_cents") == 3897
        )
    report["native_diagnostics"]["cross_account_cloudfront_lambda_url"] = {
        "passed": native_api_ok, "http_status": native_status,
        "body": native_body.decode(),
    }
    participant_shares = example.harness.client("application", "ram").get_resource_shares(
        resourceOwner="OTHER-ACCOUNTS",
    )["resourceShares"]
    owner_ids = {mapping["owner_id"] for mapping in example.subnets}
    participant_ids = {
        subnet["SubnetId"] for subnet in example.app_ec2.describe_subnets()["Subnets"]
    }
    report["native_diagnostics"]["cross_account_ram_shared_subnets"] = {
        "passed": (
            example.share["resourceShareArn"] in {
                share["resourceShareArn"] for share in participant_shares
            } and owner_ids <= participant_ids
        ),
        "participant_shares": participant_shares,
        "owner_subnets_visible_to_participant": sorted(owner_ids & participant_ids),
    }
    try:
        invalid_subnet = example.create_function(
            "odb-invalid-subnet", subnet_ids=["subnet-fffffffffffffffff"],
        )
    except ClientError as error:
        if error.response["Error"]["Code"] not in (
            "InvalidParameterValueException", "InvalidSubnetIDException",
        ):
            raise
        report["native_diagnostics"]["rejects_nonexistent_lambda_subnet"] = {
            "passed": True, "error": error.response["Error"],
        }
    else:
        report["native_diagnostics"]["rejects_nonexistent_lambda_subnet"] = {
            "passed": False, "accepted_vpc_config": invalid_subnet["VpcConfig"],
        }
        example.functions.delete_function(FunctionName="odb-invalid-subnet")
    for account in ("application", "network"):
        equal(example.harness.client(account, "s3").list_buckets()["Buckets"], [])
    for account in ("web", "network"):
        equal(example.harness.client(account, "lambda").list_functions()["Functions"], [])
    checks["resource_ownership"] = "PASS; no business Lambda in web/network or site bucket outside web"
    configuration = example.functions.get_function_configuration(FunctionName=FUNCTION)
    equal(
        configuration["CodeSha256"],
        base64.b64encode(hashlib.sha256(example.code).digest()).decode(),
    )
    checks["native_lambda_code_sha256"] = configuration["CodeSha256"]
    equal(
        example.owner_ec2.describe_vpcs(VpcIds=[example.owner_vpc])["Vpcs"][0]["CidrBlock"],
        "10.70.0.0/16",
    )
    equal(
        example.app_ec2.describe_vpcs(VpcIds=[example.canary_vpc["VpcId"]])["Vpcs"][0]["CidrBlock"],
        "10.91.0.0/16",
    )
    checks["independent_vpc_state"] = {
        "owner_cidr": "10.70.0.0/16", "participant_only_canary_cidr": "10.91.0.0/16",
    }
    with serve(example) as url:
        opener = build_opener(ProxyHandler({}))
        with opener.open(url + "/index.html", timeout=20) as response:
            equal(response.status, 200)
            equal(response.read(), example.site)
        checks["http_private_cloudfront_s3_bytes"] = {
            "sha256": hashlib.sha256(example.site).hexdigest(),
            "bytes": len(example.site),
        }
        cases = [
            ("quantity=3&unit_cents=1299&discount_percent=10", (3897, 389, 3508)),
            ("quantity=7&unit_cents=231&discount_percent=25", (1617, 404, 1213)),
        ]
        checks["http_native_business_results"] = []
        for query, expected in cases:
            with opener.open(url + "/api/quote?" + query, timeout=20) as response:
                equal(response.status, 200)
                result = json.load(response)
            equal(
                (result["subtotal_cents"], result["discount_cents"], result["total_cents"]),
                expected,
            )
            equal(result["request_id"], example.receipts[-1]["request_id"])
            checks["http_native_business_results"].append(result)
        for query in ("quantity=no&unit_cents=100", "quantity=0&unit_cents=100"):
            try:
                opener.open(url + "/api/quote?" + query, timeout=20)
            except HTTPError as error:
                with error:
                    equal(error.code, 400)
                    if "error" not in json.load(error):
                        raise AssertionError("Invalid input did not produce an error") from error
            else:
                raise AssertionError("HTTP invalid input unexpectedly succeeded")
    checks["native_business_rejects_bad_inputs"] = "PASS"
    for role in ("BusinessOrigin", "SharedNetwork"):
        binding = example.harness.roles.pop(role)
        try:
            checks[f"removed_{role}_route"] = refused(
                lambda: example.relay("/api/quote?quantity=1&unit_cents=100"),
                PermissionError,
            )
        finally:
            example.harness.roles[role] = binding
    mapping = example.subnets[0]["owner_id"]
    example.subnets[0]["owner_id"] = "subnet-fffffffffffffffff"
    try:
        checks["missing_owner_subnet"] = refused(
            lambda: example.relay("/api/quote?quantity=1&unit_cents=100"),
            ClientError, code="InvalidSubnetID.NotFound",
        )
    finally:
        example.subnets[0]["owner_id"] = mapping
    example.s3.delete_object(Bucket=BUCKET, Key="index.html")
    try:
        status, body = example.native_edge("/index.html")
        if status == 200 or body == example.site:
            raise AssertionError("Native edge returned success after deleting the origin key")
        checks["native_missing_s3_origin"] = {"http_status": status, "body": body.decode()}
    finally:
        example.s3.put_object(
            Bucket=BUCKET, Key="index.html", Body=example.site, ContentType="text/html",
        )
    example.s3.delete_bucket_policy(Bucket=BUCKET)
    try:
        status, body = example.native_edge("/index.html")
        equal(status, 403)
        checks["native_missing_origin_grant"] = {"http_status": status, "body": body.decode()}
    finally:
        example.s3.put_bucket_policy(Bucket=BUCKET, Policy=example.bucket_policy)
    configuration = example.cf.get_distribution_config(Id=example.distribution["Id"])
    broken = copy.deepcopy(configuration["DistributionConfig"])
    for origin in broken["Origins"]["Items"]:
        if origin["Id"] == "business":
            origin["DomainName"] = "missing.lambda-url.us-east-1.on.aws"
    updated = example.cf.update_distribution(
        Id=example.distribution["Id"], IfMatch=configuration["ETag"],
        DistributionConfig=broken,
    )
    try:
        checks["changed_native_origin_route"] = refused(
            lambda: example.relay("/api/quote?quantity=1&unit_cents=100"),
            AssertionError,
        )
    finally:
        example.cf.update_distribution(
            Id=example.distribution["Id"], IfMatch=updated["ETag"],
            DistributionConfig=configuration["DistributionConfig"],
        )
    example.functions.delete_function(FunctionName=FUNCTION)
    checks["deleted_business_function"] = refused(
        lambda: example.relay("/api/quote?quantity=1&unit_cents=100"),
        example.functions.exceptions.ResourceNotFoundException,
    )
    example.harness.emulators["application"].stop_backend()
    checks["stopped_native_business_backend"] = refused(
        lambda: example.relay("/api/quote?quantity=1&unit_cents=100"),
        EndpointConnectionError,
    )
    report["receipts"] = example.receipts
    report["status"] = "PASS_ADAPTED"
    return report


def run(manifest):
    with Harness(manifest, seed=7) as harness:
        example = ThreeTier(harness)
        example.deploy()
        report = exercise(example)
    report["cleanup"] = "owned emulator containers and loopback HTTP listener stopped"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=HERE / "accounts.json")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict-native", action="store_true")
    parser.add_argument("--serve", type=int, metavar="PORT")
    args = parser.parse_args()
    if args.serve is not None:
        with Harness(args.manifest, seed=7) as harness:
            example = ThreeTier(harness)
            example.deploy()
            with serve(example, args.serve) as url:
                print(f"Adapted local demo: {url} (Ctrl-C to stop)", flush=True)
                try:
                    threading.Event().wait()
                except KeyboardInterrupt:
                    pass
        return 0
    report = run(args.manifest)
    gaps = [
        name for name, result in report["native_diagnostics"].items()
        if not result["passed"]
    ]
    report["strict_native_status"] = "FAIL" if gaps else "PASS"
    if args.strict_native and gaps:
        report["status"] = "FAIL_NATIVE"
    rendered = json.dumps(report, indent=2, default=str) + "\n"
    if args.report:
        args.report.write_text(rendered)
    print(rendered, end="")
    return 1 if args.strict_native and gaps else 0


if __name__ == "__main__":
    sys.exit(main())
