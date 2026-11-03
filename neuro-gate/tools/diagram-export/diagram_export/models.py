"""Validated models for discovery, rendering, reports, and manifests."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExportConfig(BaseModel):
    """Validated CLI configuration at the application boundary."""

    model_config = ConfigDict(extra="forbid")

    docs_dir: Path
    out_dir: Path
    scale: int = Field(default=2, ge=2)
    check: bool = False
    json_output: bool = False
    timeout: int = Field(default=30, gt=0)

    @model_validator(mode="after")
    def validate_distinct_directories(self) -> "ExportConfig":
        if self.docs_dir.resolve() == self.out_dir.resolve():
            raise ValueError("docs and output directories must be different")
        return self


class DiagramSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    origin: Literal["standalone", "inline"]
    path: str = Field(min_length=1)
    document_heading: str | None = None
    block_index: int | None = Field(default=None, ge=0)
    content: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical: bool
    discovery_order: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_origin(self) -> "DiagramSource":
        if self.source_id != self.content_hash:
            raise ValueError("source_id must equal content_hash")
        if self.origin == "inline" and (self.document_heading is None or self.block_index is None):
            raise ValueError("inline sources require heading and block index")
        if self.origin == "standalone" and (self.document_heading is not None or self.block_index is not None):
            raise ValueError("standalone sources cannot have inline metadata")
        return self


class RenderedDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*\.png$")
    status: Literal["rendered", "skipped_duplicate", "failed"]
    scale: int = Field(ge=2)
    width_px: int | None = Field(default=None, ge=1)
    height_px: int | None = Field(default=None, ge=1)
    size_bytes: int | None = Field(default=None, ge=1)
    error: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> "RenderedDiagram":
        if self.status == "failed" and not self.error:
            raise ValueError("failed diagrams require an error")
        if self.status != "failed" and self.error is not None:
            raise ValueError("successful diagrams cannot have an error")
        return self


class ExportReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    tool_version: str
    generated_at: str
    docs_dir: str
    out_dir: str
    scale: int = Field(ge=2)
    check_only: bool
    total_discovered: int = Field(ge=0)
    total_unique: int = Field(ge=0)
    exported: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)
    diagrams: list[RenderedDiagram]
    success: bool

    @model_validator(mode="after")
    def validate_counts(self) -> "ExportReport":
        if self.skipped != self.total_discovered - self.total_unique:
            raise ValueError("skipped count does not match discovery counts")
        if self.exported + self.failed != self.total_unique:
            raise ValueError("exported and failed counts do not match unique count")
        return self


class ManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*\.png$")
    source_path: str = Field(min_length=1)
    origin: Literal["standalone", "inline"]
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    width_px: int = Field(ge=1)
    height_px: int = Field(ge=1)
    size_bytes: int = Field(ge=1)


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    tool_version: str
    generated_at: str
    scale: int = Field(ge=2)
    entries: list[ManifestEntry]

    @model_validator(mode="after")
    def validate_unique_entries(self) -> "Manifest":
        names = [entry.output_name for entry in self.entries]
        hashes = [entry.content_hash for entry in self.entries]
        if len(names) != len(set(names)) or len(hashes) != len(set(hashes)):
            raise ValueError("manifest entries must have unique names and hashes")
        if names != sorted(names):
            raise ValueError("manifest entries must be sorted by output_name")
        return self
