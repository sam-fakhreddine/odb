import configparser
import os
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from botocore.configprovider import ConstantProvider
from botocore.session import Session as SdkSession


def local_session(access_key: str, secret_key: str, region: str) -> boto3.Session:
    session = SdkSession()
    store = session.get_component("config_store")
    for key, value in (
        ("profile", None),
        ("config_file", os.devnull),
        ("credentials_file", os.devnull),
    ):
        store.set_config_provider(key, ConstantProvider(value))
    return boto3.Session(
        botocore_session=session,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


class Emulator:
    """Own one native process, its generated credentials and its SDK clients."""

    def __init__(self, account, port, region="us-east-1", *, image=None, engine=None):
        image = image or os.environ.get("AWS_EMULATOR_IMAGE")
        if not isinstance(image, str) or not image or image.startswith("-"):
            raise ValueError("Provide a local image or set AWS_EMULATOR_IMAGE")
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ValueError("Emulator port must be an unprivileged TCP port")
        self.engine = engine or os.environ.get("AWS_EMULATOR_ENGINE", "podman")
        if self.engine not in ("podman", "docker"):
            raise ValueError("Container engine must be podman or docker")
        self.account = account
        self.port = port
        self.region = region
        self.image = image
        self.endpoint = f"https://127.0.0.1:{port}"
        self.container_id = None
        self.directory = None
        self.session = None
        self.clients = {}

    def __enter__(self):
        if self.directory is not None:
            raise RuntimeError("Emulator is already started")
        self.directory = tempfile.TemporaryDirectory(prefix="aws-emulator-shim-")
        try:
            self.container_id = subprocess.check_output(
                [
                    self.engine, "run", "--detach", "--rm", "--pull=never",
                    "--memory=2g", "--cpus=1",
                    "-p", f"127.0.0.1:{self.port}:{self.port}",
                    "-e", "EMULATOR_TELEMETRY=off", self.image,
                    "--port", str(self.port), "--idle-timeout", "900",
                ],
                text=True,
            ).strip()
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                copied = True
                for name in ("emulator_credentials", "ca.pem"):
                    destination = Path(self.directory.name) / name
                    result = subprocess.run(
                        [
                            self.engine, "cp",
                            f"{self.container_id}:/home/emulator/.aws/emulator/"
                            f"{self.port}/{name}", str(destination),
                        ],
                        capture_output=True,
                    )
                    if result.returncode:
                        copied = False
                        break
                    destination.chmod(0o600)
                if copied:
                    break
                time.sleep(0.25)
            else:
                raise TimeoutError("Emulator credential/CA startup timed out")
            credentials = configparser.ConfigParser()
            credentials.read(Path(self.directory.name) / "emulator_credentials")
            values = credentials["default"]
            self.session = local_session(
                values["aws_access_key_id"], values["aws_secret_access_key"],
                self.region,
            )
            return self
        except BaseException as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise

    def guard_request(self, request, **kwargs):
        target = urlsplit(request.url)
        if (
            target.scheme != "https"
            or target.hostname != "127.0.0.1"
            or target.port != self.port
            or target.username is not None
            or target.password is not None
        ):
            raise ValueError(f"Non-emulator endpoint rejected: {target.hostname}")

    def client(self, service):
        if self.session is None:
            raise RuntimeError("Emulator has not started")
        if service not in self.clients:
            client = self.session.client(
                service,
                endpoint_url=self.endpoint,
                verify=str(Path(self.directory.name) / "ca.pem"),
                config=Config(
                    inject_host_prefix=False,
                    proxies={},
                    connect_timeout=3,
                    read_timeout=10,
                    retries={"total_max_attempts": 2, "mode": "standard"},
                    s3={"addressing_style": "path"},
                ),
            )
            client.meta.events.register("before-send", self.guard_request)
            self.clients[service] = client
        return self.clients[service]

    def stop_backend(self):
        if self.container_id:
            subprocess.run(
                [self.engine, "stop", "--time", "3", self.container_id],
                capture_output=True, text=True, check=True,
            )
            self.container_id = None

    def __exit__(self, error_type, error, traceback):
        cleanup_errors = []
        for client in self.clients.values():
            try:
                client.close()
            except Exception as cleanup_error:
                cleanup_errors.append(cleanup_error)
        self.clients.clear()
        self.session = None
        if self.container_id:
            try:
                self.stop_backend()
            except subprocess.CalledProcessError as cleanup_error:
                cleanup_errors.append(RuntimeError(cleanup_error.stderr.strip()))
        if self.directory:
            try:
                self.directory.cleanup()
            except OSError as cleanup_error:
                cleanup_errors.append(cleanup_error)
            else:
                self.directory = None
        if cleanup_errors:
            raise BaseExceptionGroup(
                "Emulator cleanup failed",
                ([error] if error is not None else []) + cleanup_errors,
            )
        return False
