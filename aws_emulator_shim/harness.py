import copy
import hashlib
import json
import os
import random
import re
import time
from contextlib import ExitStack
from pathlib import Path

from .runtime import Emulator


class Harness:
    """Bind caller-defined logical accounts to independent local runtimes."""

    def __init__(
        self, manifest, seed, clock=time.time, *,
        image=None, runtime_images=None, engine=None,
    ):
        self.manifest = (
            copy.deepcopy(manifest)
            if isinstance(manifest, dict)
            else json.loads(Path(manifest).read_text())
        )
        self.clock = clock
        self.random = random.Random(seed)
        self.seed = seed
        self.accounts = self.manifest["accounts"]
        if not isinstance(self.accounts, dict) or not self.accounts:
            raise ValueError("Declare at least one runtime account")
        if not isinstance(self.manifest.get("region"), str) or not self.manifest["region"]:
            raise ValueError("Declare an emulator Region")
        namespace = self.manifest.get("namespace", "emulator-shim")
        if not isinstance(namespace, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,35}", namespace):
            raise ValueError("Namespace must be 1-36 lowercase letters, digits or hyphens")
        if namespace.endswith("-"):
            raise ValueError("Namespace must not end with a hyphen")
        for account in self.accounts.values():
            if not isinstance(account, dict):
                raise ValueError("Each account requires an account_id and port")
        identities = [account.get("account_id") for account in self.accounts.values()]
        if (
            any(
                not isinstance(value, str)
                or not re.fullmatch(r"[0-9]{12}", value)
                or value == "000000000000"
                for value in identities
            )
            or len(set(identities)) != len(identities)
        ):
            raise ValueError("Logical accounts require distinct synthetic IDs")
        ports = [account.get("port") for account in self.accounts.values()]
        if (
            any(type(port) is not int or not 1024 <= port <= 65535 for port in ports)
            or len(set(ports)) != len(ports)
        ):
            raise ValueError("Runtime ports must be unique unprivileged ports")
        self.image = image or self.manifest.get("image") or os.environ.get("AWS_EMULATOR_IMAGE")
        self.engine = engine or self.manifest.get("engine") or os.environ.get(
            "AWS_EMULATOR_ENGINE", "podman"
        )
        if self.engine not in ("podman", "docker"):
            raise ValueError("Container engine must be podman or docker")
        self.runtime_images = dict(runtime_images or {})
        if set(self.runtime_images) - set(self.accounts):
            raise ValueError("Runtime image references an undeclared account")
        for name in self.accounts:
            selected = self.runtime_images.get(name, self.image)
            if not isinstance(selected, str) or not selected or selected.startswith("-"):
                raise ValueError("Provide a local image or set AWS_EMULATOR_IMAGE")
        self.roles = self.manifest.get("roles", {})
        self.bridges = self.manifest.get("bridges", {})
        for bindings in (self.roles, self.bridges):
            if not isinstance(bindings, dict):
                raise ValueError("Roles and bridges must be named mappings")
            for binding in bindings.values():
                if (
                    not isinstance(binding, dict)
                    or binding.get("source") not in self.accounts
                    or binding.get("target") not in self.accounts
                ):
                    raise ValueError("Route references an undeclared account")
        for bridge in self.bridges.values():
            if bridge["source"] == bridge["target"]:
                raise ValueError("Bridge requires two different accounts")
        self.emulators = {}
        self.stack = ExitStack()
        self.grants = set()
        self.trace = []
        self.queues = set()

    def __enter__(self):
        if self.emulators:
            raise RuntimeError("Harness instances are single-use; create a fresh instance")
        try:
            for name, account in self.accounts.items():
                self.emulators[name] = self.stack.enter_context(
                    Emulator(
                        name, account["port"], self.manifest["region"],
                        image=self.runtime_images.get(name, self.image),
                        engine=self.engine,
                    )
                )
            return self
        except BaseException as error:
            self.stack.__exit__(type(error), error, error.__traceback__)
            raise

    def __exit__(self, *error):
        return self.stack.__exit__(*error)

    def logical_id(self, account):
        if account not in self.accounts:
            raise ValueError(f"No runtime account: {account}")
        return self.accounts[account]["account_id"]

    def client(self, account, service):
        self.logical_id(account)
        if account not in self.emulators:
            raise RuntimeError("Harness has not started")
        return self.emulators[account].client(service)

    def assume_role(self, source, role):
        transition = self.roles.get(role)
        if transition is None or transition["source"] != source:
            raise PermissionError("Undeclared simulated role transition")
        if transition["target"] not in self.emulators:
            raise RuntimeError("Target emulator has not started")
        return self.emulators[transition["target"]]

    def create_queue(self, account, name):
        queue = self.client(account, "sqs").create_queue(QueueName=name)["QueueUrl"]
        self.queues.add((account, queue))
        return queue

    def _bridge(self, name):
        if name not in self.bridges:
            raise PermissionError(f"No declared simulated {name} bridge")
        return self.bridges[name]

    def relay_event(self, source, payload, queue):
        bridge = self._bridge("events")
        if source != bridge["source"]:
            raise PermissionError("Undeclared simulated event route")
        target = bridge["target"]
        if (target, queue) not in self.queues:
            raise PermissionError("Queue is not bound to the destination emulator")
        envelope = {
            "simulation": "cross-account-event-relay",
            "id": f"event-{self.random.getrandbits(64):016x}",
            "origin": self.logical_id(source),
            "destination": self.logical_id(target),
            "payload": payload,
            "time": self.clock(),
        }
        self.client(target, "sqs").send_message(
            QueueUrl=queue, MessageBody=json.dumps(envelope, sort_keys=True)
        )
        self.trace.append(envelope)
        return envelope

    def grant_transfer(self, source_bucket, source_key, target_bucket, target_key):
        self._bridge("evidence")
        grant = (source_bucket, source_key, target_bucket, target_key)
        if not all(isinstance(value, str) and value for value in grant):
            raise ValueError("Transfer resource names must be nonempty strings")
        self.grants.add(grant)

    def revoke_transfer(self, *grant):
        self.grants.remove(grant)

    def transfer(self, source_bucket, source_key, target_bucket, target_key):
        grant = (source_bucket, source_key, target_bucket, target_key)
        if grant not in self.grants:
            raise PermissionError("No matching simulated transfer grant")
        bridge = self._bridge("evidence")
        source = self.client(bridge["source"], "s3")
        target = self.client(bridge["target"], "s3")
        with source.get_object(Bucket=source_bucket, Key=source_key)["Body"] as body:
            data = body.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise ValueError("Transfer fixtures are limited to 1 MiB")
        receipt = {
            "simulation": "cross-account-object-transfer",
            "source_account": self.logical_id(bridge["source"]),
            "target_account": self.logical_id(bridge["target"]),
            "source_bucket": source_bucket,
            "source_key": source_key,
            "target_bucket": target_bucket,
            "target_key": target_key,
            "sha256": hashlib.sha256(data).hexdigest(),
            "status": "attempted",
        }
        self.trace.append(receipt)
        try:
            existing = target.get_object(Bucket=target_bucket, Key=target_key)
        except target.exceptions.NoSuchKey:
            target.put_object(Bucket=target_bucket, Key=target_key, Body=data)
        else:
            with existing["Body"] as body:
                if body.read() != data:
                    raise ValueError("Transfer would overwrite different evidence")
        with target.get_object(Bucket=target_bucket, Key=target_key)["Body"] as body:
            if body.read() != data:
                raise ValueError("Destination evidence bytes do not match")
        receipt["status"] = "completed"
        return receipt
