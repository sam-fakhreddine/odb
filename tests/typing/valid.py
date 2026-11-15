"""Positive static consumer; also checked against the installed wheel."""

from typing import assert_type

from aws_emulator_shim import Account, Manifest, Route, parse_manifest

account = Account(account_id="111111111111", port=9297)
manifest = Manifest(region="us-east-1", accounts={"app": account})
route = Route(source="app", target="app")

assert_type(manifest.accounts["app"], Account)
assert_type(manifest.accounts["app"].port, int)
assert_type(manifest.accounts["app"].account_id, str)
assert_type(parse_manifest(manifest), Manifest)
