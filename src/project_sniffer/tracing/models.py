from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from project_sniffer.parsing import (
    ImportEvidence,
)


class ImportResolutionStatus(
    str,
    Enum,
):
    RESOLVED_INTERNAL = "resolved_internal"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    INVALID_RELATIVE_IMPORT = (
        "invalid_relative_import"
    )

class DependencyKind(
    str,
    Enum,
):
    IMPORT = "import"


@dataclass(frozen=True)
class DependencyEdge:
    source_path: str
    target_path: str
    kind: DependencyKind
    line: int
    scope: str | None
    resolution: ImportResolution


@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[str, ...]
    import_resolutions: tuple[
        ImportResolution,
        ...,
    ]
    edges: tuple[
        DependencyEdge,
        ...,
    ]

@dataclass(frozen=True)
class ImportResolution:
    source_path: str
    evidence: ImportEvidence
    requested_modules: tuple[str, ...]
    status: ImportResolutionStatus
    target_path: str | None = None
    candidate_paths: tuple[str, ...] = ()
