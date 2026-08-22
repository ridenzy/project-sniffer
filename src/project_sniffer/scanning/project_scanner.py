from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from project_sniffer.scanning.ignore_matcher import (
    IgnoreMatcher,
)
from project_sniffer.scanning.models import (
    ScanManifest,
    ScannedFile,
)


def _normalize_excluded_directories(
    excluded_directories: Iterable[Path],
) -> tuple[Path, ...]:
    return tuple(
        path.expanduser().resolve()
        for path in excluded_directories
    )


def _is_excluded_directory(
    directory: Path,
    excluded_directories: tuple[Path, ...],
) -> bool:
    candidate = directory.resolve()

    return any(
        candidate == excluded
        for excluded in excluded_directories
    )


def scan_project(
    root_path: str | Path,
    ignore: dict[str, list[str]] | None = None,
    *,
    excluded_directories: Iterable[Path] = (),
) -> ScanManifest:
    """
    Walk the target project once and return a deterministic scan manifest.

    Current ignore support covers exact basename rules and shell-style glob
    patterns inside IGNORE_FOLDERS and IGNORE_FILES.

    Project-relative path rules and .gitignore semantics remain separate
    follow-on work.
    """

    project_path = (
        Path(
            root_path
        )
        .expanduser()
        .resolve()
    )

    matcher = IgnoreMatcher.from_config(
        ignore
    )

    excluded = (
        _normalize_excluded_directories(
            excluded_directories
        )
    )

    directories: list[str] = []
    scanned_files: list[ScannedFile] = []

    for root, dirs, files in os.walk(
        project_path,
        topdown=True,
        followlinks=False,
    ):
        current_root = Path(
            root
        )

        kept_directories: list[str] = []

        for directory_name in sorted(
            dirs
        ):
            candidate = (
                current_root
                / directory_name
            )

            if matcher.matches_folder(
                directory_name
            ):
                continue

            if _is_excluded_directory(
                candidate,
                excluded,
            ):
                continue

            kept_directories.append(
                directory_name
            )

        dirs[:] = kept_directories

        relative_root = (
            current_root.relative_to(
                project_path
            )
        )

        if relative_root.parts:
            directories.append(
                relative_root.as_posix()
            )

        for filename in sorted(
            files
        ):
            if matcher.matches_file(
                filename
            ):
                continue

            absolute_path = (
                current_root
                / filename
            )

            relative_path = (
                absolute_path.relative_to(
                    project_path
                )
                .as_posix()
            )

            scanned_files.append(
                ScannedFile(
                    absolute_path=absolute_path,
                    relative_path=relative_path,
                )
            )

    return ScanManifest(
        project_path=project_path,
        directories=tuple(
            directories
        ),
        files=tuple(
            scanned_files
        ),
    )
