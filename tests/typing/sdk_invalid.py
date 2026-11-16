"""Three intentional mypy errors from the SDK surface; never execute this fixture."""

from aws_emulator_shim.runtime import local_session

session = local_session(access_key="local-key", secret_key="local-secret", region="us-east-1")
session.client("s3").list_buckets(unexpected_kwarg=True)
session.client("s3").get_object(Bucket=123, Key="object")
session.client("sts").assume_role(RoleArn=123, RoleSessionName="session")
