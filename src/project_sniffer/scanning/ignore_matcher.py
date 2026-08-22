from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Mapping, Sequence


@dataclass(frozen=True)
class IgnoreMatcher:
    folder_patterns: tuple[str, ...]
    file_patterns: tuple[str, ...]

    @classmethod
    def from_config(
        cls,
        ignore: Mapping[str, Sequence[str]] | None,
    ) -> "IgnoreMatcher":
        ignore = ignore or {}

        return cls(
            folder_patterns=tuple(
                ignore.get(
                    "IGNORE_FOLDERS",
                    (),
                )
            ),
            file_patterns=tuple(
                ignore.get(
                    "IGNORE_FILES",
                    (),
                )
            ),
        )

    def matches_folder(
        self,
        name: str,
    ) -> bool:
        return any(
            fnmatchcase(
                name,
                pattern,
            )
            for pattern in self.folder_patterns
        )

    def matches_file(
        self,
        name: str,
    ) -> bool:
        return any(
            fnmatchcase(
                name,
                pattern,
            )
            for pattern in self.file_patterns
        )
