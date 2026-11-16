"""Positive static SDK consumer; also checked against the installed wheel.

Constructs a typed local session and its clients only. It never issues a
network call, so executing it does not contact AWS or an emulator.
"""
from typing import assert_type

from mypy_boto3_s3 import S3Client
from mypy_boto3_sts import STSClient

from aws_emulator_shim.runtime import local_session

session = local_session(access_key="local-key", secret_key="local-secret", region="us-east-1")
s3: S3Client = session.client("s3")
sts: STSClient = session.client("sts")

assert_type(s3, S3Client)
assert_type(sts, STSClient)
# Referenced, not called: a presigner exists and is typed without any request.
assert_type(s3.can_paginate("list_objects_v2"), bool)
assert_type(sts.can_paginate("assume_role"), bool)
