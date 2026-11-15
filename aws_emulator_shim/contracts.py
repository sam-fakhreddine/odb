"""Strict inventory types and parsers; no emulator or AWS operations."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, NoReturn, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

NATIVE_ACCOUNT_ID = "000000000000"
Name = Annotated[str, StringConstraints(min_length=1, pattern=r"^\S+$")]
LogicalAccountId = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{12}$"),
    Field(json_schema_extra={"not": {"const": NATIVE_ACCOUNT_ID}}),
]
Port = Annotated[int, Field(ge=1024, le=65535)]
Engine = Literal["podman", "docker"]
BridgeName = Literal["events", "evidence"]
Namespace = Annotated[
    str, StringConstraints(pattern=r"^[a-z](?:[a-z0-9-]{0,34}[a-z0-9])?$"),
]
Image = Annotated[str, StringConstraints(min_length=1, pattern=r"^[^-\s]\S*$")]


class StrictContract(BaseModel):
    model_config = ConfigDict(
        strict=True, extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )


class Account(StrictContract):
    account_id: LogicalAccountId
    port: Port

    @field_validator("account_id")
    @classmethod
    def synthetic_identity(cls, value: str) -> str:
        if value == NATIVE_ACCOUNT_ID:
            raise PydanticCustomError("reserved_account_id", "Use a synthetic logical account ID")
        return value


class Route(StrictContract):
    source: Name
    target: Name


class Manifest(StrictContract):
    schema_version: Literal[1] = 1
    region: Name
    namespace: Namespace = "emulator-shim"
    accounts: Annotated[Mapping[Name, Account], Field(min_length=1)]
    roles: Mapping[Name, Route] = Field(default_factory=dict)
    bridges: Mapping[BridgeName, Route] = Field(default_factory=dict)
    image: Image | None = None
    engine: Engine | None = None

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version_type(cls, value: object) -> object:
        if type(value) is not int:
            raise PydanticCustomError("schema_version_type", "Schema version must be an integer")
        return value

    @field_validator("accounts")
    @classmethod
    def freeze_accounts(cls, value: Mapping[str, Account]) -> Mapping[str, Account]:
        return MappingProxyType(dict(value))

    @field_validator("roles")
    @classmethod
    def freeze_roles(cls, value: Mapping[str, Route]) -> Mapping[str, Route]:
        return MappingProxyType(dict(value))

    @field_validator("bridges")
    @classmethod
    def freeze_bridges(
        cls, value: Mapping[BridgeName, Route],
    ) -> Mapping[BridgeName, Route]:
        return MappingProxyType(dict(value))

    @field_serializer("accounts")
    def serialize_accounts(self, value: Mapping[str, Account]) -> dict[str, Account]:
        return dict(value)

    @field_serializer("roles")
    def serialize_roles(self, value: Mapping[str, Route]) -> dict[str, Route]:
        return dict(value)

    @field_serializer("bridges")
    def serialize_bridges(
        self, value: Mapping[BridgeName, Route],
    ) -> dict[BridgeName, Route]:
        return dict(value)

    @model_validator(mode="after")
    def consistent_routes(self) -> Self:
        identities = [account.account_id for account in self.accounts.values()]
        ports = [account.port for account in self.accounts.values()]
        if len(set(identities)) != len(identities):
            raise PydanticCustomError("duplicate_account_id", "Logical account IDs must be unique")
        if len(set(ports)) != len(ports):
            raise PydanticCustomError("duplicate_port", "Runtime ports must be unique")
        for routes in (self.roles, self.bridges):
            for route in routes.values():
                if route.source not in self.accounts or route.target not in self.accounts:
                    raise PydanticCustomError("unknown_route_account", "Route account is undeclared")
        if any(route.source == route.target for route in self.bridges.values()):
            raise PydanticCustomError("same_account_bridge", "Bridge requires different accounts")
        return self


@dataclass(frozen=True)
class ManifestIssue:
    path: tuple[str | int, ...]
    code: str


class ManifestError(ValueError):
    """Public diagnostic contains only allowlisted field paths and error codes."""

    def __init__(self, issues: tuple[ManifestIssue, ...]) -> None:
        self.issues = issues
        details = "; ".join(
            f"{'.'.join(map(str, issue.path)) or 'manifest'} [{issue.code}]"
            for issue in issues
        )
        super().__init__(f"Invalid manifest: {details}")


def parse_manifest(data: object) -> Manifest:
    """Validate unknown input without coercion or values in public diagnostics."""
    try:
        return Manifest.model_validate(data)
    except ValidationError as error:
        fields = {
            "schema_version", "region", "namespace", "accounts", "roles", "bridges",
            "image", "engine", "account_id", "port", "source", "target",
        }
        issues = tuple(
            ManifestIssue(
                tuple(part if part in fields else "*" for part in item["loc"]),
                item["type"],
            )
            for item in error.errors(include_url=False, include_context=False, include_input=False)
        )
        raise ManifestError(issues) from None


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError((ManifestIssue((), "duplicate_json_key"),))
        result[key] = value
    return result


def _reject_constant(_value: str) -> NoReturn:
    raise ManifestError((ManifestIssue((), "non_finite_json_number"),))


def load_manifest(path: str | Path) -> Manifest:
    """Read strict UTF-8 JSON; file I/O failures remain explicit."""
    try:
        data: object = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_pairs, parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ManifestError((ManifestIssue((), "invalid_json"),)) from None
    return parse_manifest(data)
