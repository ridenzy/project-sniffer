from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from project_sniffer.scanning.models import (
    ScannedFile,
)


class FileReadStatus(str, Enum):
    TEXT = "text"
    BINARY = "binary"
    SYMLINK = "symlink"
    ESCAPED_SYMLINK = "escaped_symlink"
    UNREADABLE = "unreadable"
    OUTSIDE_PROJECT = "outside_project"
    PATH_MISMATCH = "path_mismatch"


@dataclass(frozen=True)
class FileReadResult:
    scanned_file: ScannedFile
    status: FileReadStatus
    content: str | None
    resolved_path: Path | None
    size_bytes: int | None
    is_symlink: bool
    error_type: str | None = None
    error_message: str | None = None
