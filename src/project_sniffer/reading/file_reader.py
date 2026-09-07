from __future__ import annotations

import os
from pathlib import Path

from project_sniffer.reading.models import (
    FileReadResult,
    FileReadStatus,
)
from project_sniffer.scanning.models import (
    ScanManifest,
    ScannedFile,
)


def _is_valid_text_char(
    char: str,
) -> bool:
    codepoint = ord(
        char
    )

    return (
        codepoint == 0x09
        or codepoint == 0x0A
        or codepoint == 0x0D
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def _clean_text(
    text: str,
) -> str:
    return "".join(
        char
        for char in text
        if _is_valid_text_char(
            char
        )
    )


def _lexical_absolute_path(
    path: Path,
) -> Path:
    return Path(
        os.path.abspath(
            os.fspath(
                path
            )
        )
    )


def _is_within_project(
    path: Path,
    project_path: Path,
) -> bool:
    try:
        path.relative_to(
            project_path
        )
    except ValueError:
        return False

    return True


def _result(
    *,
    scanned_file: ScannedFile,
    status: FileReadStatus,
    content: str | None = None,
    resolved_path: Path | None = None,
    size_bytes: int | None = None,
    is_symlink: bool = False,
    error_type: str | None = None,
    error_message: str | None = None,
) -> FileReadResult:
    return FileReadResult(
        scanned_file=scanned_file,
        status=status,
        content=content,
        resolved_path=resolved_path,
        size_bytes=size_bytes,
        is_symlink=is_symlink,
        error_type=error_type,
        error_message=error_message,
    )


def read_scanned_file(
    *,
    project_path: Path,
    scanned_file: ScannedFile,
) -> FileReadResult:
    """
    Safely classify and read one discovered file.

    File symlinks are never followed for source content. Internal symlinks are
    classified as symlinks; symlinks resolving outside the project root are
    classified separately as escaped symlinks.
    """

    project_root = (
        project_path
        .expanduser()
        .resolve()
    )

    candidate = (
        _lexical_absolute_path(
            scanned_file.absolute_path
        )
    )

    try:
        lexical_relative = (
            candidate.relative_to(
                project_root
            )
        )
    except ValueError:
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.OUTSIDE_PROJECT
            ),
        )

    if (
        lexical_relative.as_posix()
        != scanned_file.relative_path
    ):
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.PATH_MISMATCH
            ),
        )

    if candidate.is_symlink():
        try:
            resolved_path = (
                candidate.resolve(
                    strict=False
                )
            )
        except OSError as error:
            return _result(
                scanned_file=scanned_file,
                status=(
                    FileReadStatus.UNREADABLE
                ),
                is_symlink=True,
                error_type=type(
                    error
                ).__name__,
                error_message=str(
                    error
                ),
            )

        if not _is_within_project(
            resolved_path,
            project_root,
        ):
            return _result(
                scanned_file=scanned_file,
                status=(
                    FileReadStatus.ESCAPED_SYMLINK
                ),
                resolved_path=resolved_path,
                is_symlink=True,
            )

        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.SYMLINK
            ),
            resolved_path=resolved_path,
            is_symlink=True,
        )

    try:
        resolved_path = candidate.resolve(
            strict=True
        )
    except OSError as error:
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.UNREADABLE
            ),
            error_type=type(
                error
            ).__name__,
            error_message=str(
                error
            ),
        )

    if not _is_within_project(
        resolved_path,
        project_root,
    ):
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.OUTSIDE_PROJECT
            ),
            resolved_path=resolved_path,
        )

    try:
        data = resolved_path.read_bytes()
    except OSError as error:
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.UNREADABLE
            ),
            resolved_path=resolved_path,
            error_type=type(
                error
            ).__name__,
            error_message=str(
                error
            ),
        )

    size_bytes = len(
        data
    )

    if b"\x00" in data[:2048]:
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.BINARY
            ),
            resolved_path=resolved_path,
            size_bytes=size_bytes,
        )

    content = _clean_text(
        data.decode(
            "utf-8",
            errors="ignore",
        )
    )

    return _result(
        scanned_file=scanned_file,
        status=FileReadStatus.TEXT,
        content=content,
        resolved_path=resolved_path,
        size_bytes=size_bytes,
    )


def read_manifest_files(
    manifest: ScanManifest,
) -> tuple[FileReadResult, ...]:
    return tuple(
        read_scanned_file(
            project_path=manifest.project_path,
            scanned_file=scanned_file,
        )
        for scanned_file in manifest.files
    )
