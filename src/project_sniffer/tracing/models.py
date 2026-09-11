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
    RESOLVED_INTERNAL = "resolved_internal"
    POTENTIAL_INTERNAL = "potential_internal"
    SHADOWED = "shadowed"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    DYNAMIC = "dynamic"

class CallResolutionProof(
    str,
    Enum,
):
    INTERNAL_IMPORT_BINDING = (
        "internal_import_binding"
    )

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
    CALL = "call"


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
    resolved_target: CallTarget | None = None
    proof: CallResolutionProof | None = None
    shadowed_by: CallShadowReason | None = None


@dataclass(frozen=True)
class DependencyEdge:
    source_path: str
    target_path: str
    kind: DependencyKind
    line: int
    scope: str | None
    resolution: (
        ImportResolution
        | CallResolution
    )
    target_symbol: str | None = None


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

@dataclass(frozen=True)
class CallEndpoint:
    path: str
    symbol: str | None


@dataclass(frozen=True)
class CallIndexEntry:
    endpoint: CallEndpoint
    edges: tuple[
        DependencyEdge,
        ...,
    ]


@dataclass(frozen=True)
class CallIndex:
    outbound: tuple[
        CallIndexEntry,
        ...,
    ]
    inbound: tuple[
        CallIndexEntry,
        ...,
    ]