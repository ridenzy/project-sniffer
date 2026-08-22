from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from project_sniffer.scanning.gitignore_matcher import (
    GitIgnoreMatcher,
)
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

    Configuration ignore rules support exact basenames, basename globs, and
    project-relative path patterns.

    Target-project .gitignore files are loaded as directories are reached, so
    deeper .gitignore files can override matching rules inherited from parent
    directories.
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

    gitignore_matcher = (
        GitIgnoreMatcher()
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

        relative_root_path = (
            current_root.relative_to(
                project_path
            )
        )

        relative_root = (
            ""
            if not relative_root_path.parts
            else relative_root_path.as_posix()
        )

        gitignore_matcher.load_directory(
            directory_path=current_root,
            relative_directory=relative_root,
        )

        kept_directories: list[str] = []

        for directory_name in sorted(
            dirs
        ):
            candidate = (
                current_root
                / directory_name
            )

            relative_directory = (
                candidate.relative_to(
                    project_path
                )
                .as_posix()
            )

            if matcher.matches_folder(
                directory_name,
                relative_directory,
            ):
                continue

            if _is_excluded_directory(
                candidate,
                excluded,
            ):
                continue

            if gitignore_matcher.matches_directory(
                relative_directory
            ):
                continue

            kept_directories.append(
                directory_name
            )

        dirs[:] = kept_directories

        if relative_root:
            directories.append(
                relative_root
            )

        for filename in sorted(
            files
        ):
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

            if matcher.matches_file(
                filename,
                relative_path,
            ):
                continue

            if gitignore_matcher.matches_file(
                relative_path
            ):
                continue

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
