from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScannedFile:
    absolute_path: Path
    relative_path: str


@dataclass(frozen=True)
class ScanManifest:
    project_path: Path
    directories: tuple[str, ...]
    files: tuple[ScannedFile, ...]
