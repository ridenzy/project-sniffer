from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pathspec import GitIgnoreSpec

from project_sniffer.scanning.errors import (
    ScanError,
)


@dataclass(frozen=True)
class GitIgnoreRuleSet:
    base_directory: str
    source_path: Path
    spec: GitIgnoreSpec


class GitIgnoreMatcher:
    def __init__(
        self,
    ) -> None:
        self._rule_sets: list[
            GitIgnoreRuleSet
        ] = []

    def load_directory(
        self,
        *,
        directory_path: Path,
        relative_directory: str,
    ) -> None:
        source_path = (
            directory_path
            / ".gitignore"
        )

        if source_path.is_symlink():
            return

        if not source_path.is_file():
            return

        try:
            lines = source_path.read_text(
                encoding="utf-8-sig"
            ).splitlines()

        except (
            OSError,
            UnicodeError,
        ) as error:
            raise ScanError(
                "Could not read target-project "
                f".gitignore at {source_path}: {error}"
            ) from error

        try:
            spec = GitIgnoreSpec.from_lines(
                lines
            )

        except ValueError as error:
            raise ScanError(
                "Could not parse target-project "
                f".gitignore at {source_path}: {error}"
            ) from error

        self._rule_sets.append(
            GitIgnoreRuleSet(
                base_directory=(
                    relative_directory
                    .replace("\\", "/")
                    .strip("/")
                ),
                source_path=source_path,
                spec=spec,
            )
        )

    def _path_relative_to_rule_set(
        self,
        *,
        relative_path: str,
        base_directory: str,
    ) -> str | None:
        normalized = (
            relative_path
            .replace("\\", "/")
            .lstrip("/")
        )

        if not base_directory:
            return normalized

        if normalized == base_directory:
            return ""

        prefix = (
            base_directory
            + "/"
        )

        if not normalized.startswith(
            prefix
        ):
            return None

        return normalized[
            len(
                prefix
            ):
        ]

    def _is_ignored(
        self,
        *,
        relative_path: str,
        is_directory: bool,
    ) -> bool:
        ignored = False

        for rule_set in self._rule_sets:
            candidate = (
                self._path_relative_to_rule_set(
                    relative_path=relative_path,
                    base_directory=(
                        rule_set.base_directory
                    ),
                )
            )

            if candidate is None:
                continue

            if is_directory:
                candidate = (
                    candidate.rstrip("/")
                    + "/"
                )

            result = rule_set.spec.check_file(
                candidate
            )

            if result.include is not None:
                ignored = bool(
                    result.include
                )

        return ignored

    def matches_directory(
        self,
        relative_path: str,
    ) -> bool:
        return self._is_ignored(
            relative_path=relative_path,
            is_directory=True,
        )

    def matches_file(
        self,
        relative_path: str,
    ) -> bool:
        return self._is_ignored(
            relative_path=relative_path,
            is_directory=False,
        )
