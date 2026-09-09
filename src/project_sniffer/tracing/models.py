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


@dataclass(frozen=True)
class ImportResolution:
    source_path: str
    evidence: ImportEvidence
    requested_modules: tuple[str, ...]
    status: ImportResolutionStatus
    target_path: str | None = None
    candidate_paths: tuple[str, ...] = ()
