from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from project_sniffer.parsing import (
    CallEvidence,
    ImportEvidence,
    SymbolKind,
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


class CallResolutionStatus(
    str,
    Enum,
):
    POTENTIAL_INTERNAL = "potential_internal"
    SHADOWED = "shadowed"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    DYNAMIC = "dynamic"

class CallShadowReason(
    str,
    Enum,
):
    PARAMETER = "parameter"
    ASSIGNMENT = "assignment"
    IMPORT = "import"
    NONLOCAL = "nonlocal"
    FREE = "free"
    LOCAL = "local"

class DependencyKind(
    str,
    Enum,
):
    IMPORT = "import"


@dataclass(frozen=True)
class ImportResolution:
    source_path: str
    evidence: ImportEvidence
    requested_modules: tuple[str, ...]
    status: ImportResolutionStatus
    target_path: str | None = None
    candidate_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class CallTarget:
    source_path: str
    qualified_name: str
    kind: SymbolKind
    line: int


@dataclass(frozen=True)
class CallResolution:
    source_path: str
    evidence: CallEvidence
    status: CallResolutionStatus
    candidate_targets: tuple[
        CallTarget,
        ...,
    ] = ()
    shadowed_by: CallShadowReason | None = None


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
    call_resolutions: tuple[
        CallResolution,
        ...,
    ]
    edges: tuple[
        DependencyEdge,
        ...,
    ]