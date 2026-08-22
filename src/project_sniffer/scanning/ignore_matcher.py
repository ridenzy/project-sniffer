from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Mapping, Sequence

from pathspec import GitIgnoreSpec

from project_sniffer.scanning.errors import (
    ScanError,
)


def _is_project_relative_pattern(
    pattern: str,
) -> bool:
    return "/" in pattern


def _literalize_gitignore_control(
    pattern: str,
) -> str:
    if pattern.startswith(
        (
            "!",
            "#",
        )
    ):
        return (
            "\\"
            + pattern
        )

    return pattern


def _build_path_spec(
    patterns: tuple[str, ...],
    *,
    label: str,
) -> GitIgnoreSpec | None:
    path_patterns = [
        _literalize_gitignore_control(
            pattern
        )
        for pattern in patterns
        if _is_project_relative_pattern(
            pattern
        )
    ]

    if not path_patterns:
        return None

    try:
        return GitIgnoreSpec.from_lines(
            path_patterns
        )

    except ValueError as error:
        raise ScanError(
            "Could not parse project-relative "
            f"{label} ignore rules: {error}"
        ) from error


@dataclass(frozen=True)
class IgnoreMatcher:
    folder_patterns: tuple[str, ...]
    file_patterns: tuple[str, ...]
    folder_path_spec: GitIgnoreSpec | None
    file_path_spec: GitIgnoreSpec | None

    @classmethod
    def from_config(
        cls,
        ignore: Mapping[str, Sequence[str]] | None,
    ) -> "IgnoreMatcher":
        ignore = ignore or {}

        folder_patterns = tuple(
            ignore.get(
                "IGNORE_FOLDERS",
                (),
            )
        )

        file_patterns = tuple(
            ignore.get(
                "IGNORE_FILES",
                (),
            )
        )

        return cls(
            folder_patterns=folder_patterns,
            file_patterns=file_patterns,
            folder_path_spec=(
                _build_path_spec(
                    folder_patterns,
                    label="folder",
                )
            ),
            file_path_spec=(
                _build_path_spec(
                    file_patterns,
                    label="file",
                )
            ),
        )

    def matches_folder(
        self,
        name: str,
        relative_path: str | None = None,
    ) -> bool:
        basename_match = any(
            fnmatchcase(
                name,
                pattern,
            )
            for pattern in self.folder_patterns
            if not _is_project_relative_pattern(
                pattern
            )
        )

        if basename_match:
            return True

        if (
            relative_path is None
            or self.folder_path_spec is None
        ):
            return False

        normalized = (
            relative_path
            .replace("\\", "/")
            .strip("/")
        )

        if not normalized:
            return False

        return self.folder_path_spec.match_file(
            normalized
            + "/"
        )

    def matches_file(
        self,
        name: str,
        relative_path: str | None = None,
    ) -> bool:
        basename_match = any(
            fnmatchcase(
                name,
                pattern,
            )
            for pattern in self.file_patterns
            if not _is_project_relative_pattern(
                pattern
            )
        )

        if basename_match:
            return True

        if (
            relative_path is None
            or self.file_path_spec is None
        ):
            return False

        normalized = (
            relative_path
            .replace("\\", "/")
            .lstrip("/")
        )

        return self.file_path_spec.match_file(
            normalized
        )
