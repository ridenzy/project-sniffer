from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from project_sniffer.scanning import (
    ScanManifest,
)


def _parent_key(
    relative_path: str,
) -> str:
    parent = PurePosixPath(
        relative_path
    ).parent

    if str(
        parent
    ) == ".":
        return ""

    return parent.as_posix()


def build_architecture(
    manifest: ScanManifest,
) -> str:
    """
    Build the project tree from the shared scan manifest.

    This function performs no filesystem walk of its own.
    """

    directories_by_parent: dict[
        str,
        list[str],
    ] = defaultdict(
        list
    )

    files_by_parent: dict[
        str,
        list[str],
    ] = defaultdict(
        list
    )

    for relative_directory in manifest.directories:
        path = PurePosixPath(
            relative_directory
        )

        directories_by_parent[
            _parent_key(
                relative_directory
            )
        ].append(
            path.name
        )

    for scanned_file in manifest.files:
        path = PurePosixPath(
            scanned_file.relative_path
        )

        files_by_parent[
            _parent_key(
                scanned_file.relative_path
            )
        ].append(
            path.name
        )

    lines: list[str] = []

    project_name = (
        manifest.project_path.name
        or "root"
    )

    def render_directory(
        relative_directory: str,
        display_name: str,
        level: int,
    ) -> None:
        indent = (
            "│   "
            * level
        )

        lines.append(
            f"{indent}{display_name}/"
        )

        subindent = (
            "│   "
            * (
                level
                + 1
            )
        )

        for filename in sorted(
            files_by_parent.get(
                relative_directory,
                [],
            )
        ):
            lines.append(
                f"{subindent}{filename}"
            )

        for directory_name in sorted(
            directories_by_parent.get(
                relative_directory,
                [],
            )
        ):
            child_relative = (
                directory_name
                if not relative_directory
                else (
                    f"{relative_directory}/"
                    f"{directory_name}"
                )
            )

            render_directory(
                child_relative,
                directory_name,
                level + 1,
            )

    render_directory(
        "",
        project_name,
        0,
    )

    return "\n".join(
        lines
    )
