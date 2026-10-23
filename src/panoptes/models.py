"""Typed, serializable domain models used throughout PANOPTES."""
from __future__ import annotations
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
import orjson
from pydantic import BaseModel, ConfigDict, Field


class AssetType(StrEnum):
    """Kinds of observable assets tracked by PANOPTES."""
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    NETWORK = "network"
    URL = "url"
    HOST = "host"
    SERVICE = "service"
    CERTIFICATE = "certificate"
    TECHNOLOGY = "technology"
    REPOSITORY = "repository"
    UNKNOWN = "unknown"


class EdgeType(StrEnum):
    """Relationship types in the asset graph."""
    RESOLVES_TO = "resolves_to"
    HOSTS = "hosts"
    SERVES = "serves"
    REDIRECTS_TO = "redirects_to"
    RELATED_TO = "related_to"
    USES = "uses"
    DISCOVERED_FROM = "discovered_from"


class FindingSeverity(StrEnum):
    """Normalized finding severity."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Provenance(BaseModel):
    """Evidence describing where and when an observation originated."""
    model_config = ConfigDict(extra="forbid")
    source: str = Field(min_length=1)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reference: str | None = None
    detail: str | None = None


class Asset(BaseModel):
    """A normalized asset node with temporal and provenance metadata."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(min_length=1)
    value: str = Field(min_length=1)
    type: AssetType = AssetType.UNKNOWN
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()

    def to_json(self) -> bytes:
        """Serialize to UTF-8 JSON bytes."""
        return orjson.dumps(self.model_dump(mode="json"))


class Edge(BaseModel):
    """A directed relationship between two asset identifiers."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    type: EdgeType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provenance: tuple[Provenance, ...] = ()

    def to_json(self) -> bytes:
        """Serialize to UTF-8 JSON bytes."""
        return orjson.dumps(self.model_dump(mode="json"))


class Finding(BaseModel):
    """A security-relevant observation produced by a source or probe."""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    severity: FindingSeverity = FindingSeverity.INFO
    asset_ids: tuple[str, ...] = ()
    source: str = Field(min_length=1)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    references: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> bytes:
        """Serialize to UTF-8 JSON bytes."""
        return orjson.dumps(self.model_dump(mode="json"))


class RunResult(BaseModel):
    """Summary and outcome of a single PANOPTES run."""
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1)
    target: str = Field(min_length=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    assets_discovered: int = Field(default=0, ge=0)
    edges_discovered: int = Field(default=0, ge=0)
    findings: tuple[Finding, ...] = ()
    errors: tuple[str, ...] = ()
    success: bool = True

    def to_json(self) -> bytes:
        """Serialize to UTF-8 JSON bytes."""
        return orjson.dumps(self.model_dump(mode="json"))
