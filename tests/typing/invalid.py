"""Four intentional mypy errors; never execute this negative-control fixture."""

from aws_emulator_shim import Account

Account(account_id=111111111111, port="9297")
account = Account(account_id="111111111111", port=9297, surprise=True)
_ = account.not_a_field
