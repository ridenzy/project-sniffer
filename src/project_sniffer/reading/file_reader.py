from __future__ import annotations

import os
import stat
from pathlib import Path

from project_sniffer.reading.models import (
    FileReadResult,
    FileReadStatus,
)
from project_sniffer.scanning.models import (
    ScanManifest,
    ScannedFile,
)


DEFAULT_MAX_SOURCE_BYTES = 8 * 1024 * 1024


def _validate_max_source_bytes(
    max_source_bytes: int,
) -> int:
    if (
        isinstance(
            max_source_bytes,
            bool,
        )
        or not isinstance(
            max_source_bytes,
            int,
        )
        or max_source_bytes < 1
    ):
        raise ValueError(
            "max_source_bytes must be a positive integer"
        )

    return max_source_bytes


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
    max_source_bytes: int = (
        DEFAULT_MAX_SOURCE_BYTES
    ),
) -> FileReadResult:
    """
    Safely classify and read one discovered file.

    File symlinks are never followed for source content. Internal symlinks are
    classified as symlinks; symlinks resolving outside the project root are
    classified separately as escaped symlinks. Oversized source files are
    classified without loading their full content into memory.
    """

    max_source_bytes = (
        _validate_max_source_bytes(
            max_source_bytes
        )
    )

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
        file_stat = resolved_path.stat()
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

    if not stat.S_ISREG(
        file_stat.st_mode
    ):
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.UNREADABLE
            ),
            resolved_path=resolved_path,
            size_bytes=file_stat.st_size,
            error_type="UnsupportedFileType",
            error_message=(
                "source path is not a regular file"
            ),
        )

    try:
        with resolved_path.open(
            "rb"
        ) as file_handle:
            size_bytes = os.fstat(
                file_handle.fileno()
            ).st_size

            sample_limit = min(
                2048,
                max_source_bytes + 1,
            )

            sample = file_handle.read(
                sample_limit
            )

            if b"\x00" in sample:
                return _result(
                    scanned_file=scanned_file,
                    status=(
                        FileReadStatus.BINARY
                    ),
                    resolved_path=resolved_path,
                    size_bytes=size_bytes,
                )

            if size_bytes > max_source_bytes:
                return _result(
                    scanned_file=scanned_file,
                    status=(
                        FileReadStatus.OVERSIZED
                    ),
                    resolved_path=resolved_path,
                    size_bytes=size_bytes,
                )

            remaining_limit = (
                max_source_bytes
                + 1
                - len(sample)
            )

            remainder = file_handle.read(
                remaining_limit
            )

            data = sample + remainder

            observed_size = os.fstat(
                file_handle.fileno()
            ).st_size

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

    size_bytes = max(
        size_bytes,
        observed_size,
        len(data),
    )

    if (
        len(data) > max_source_bytes
        or observed_size > max_source_bytes
    ):
        return _result(
            scanned_file=scanned_file,
            status=(
                FileReadStatus.OVERSIZED
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
    *,
    max_source_bytes: int = (
        DEFAULT_MAX_SOURCE_BYTES
    ),
) -> tuple[FileReadResult, ...]:
    return tuple(
        read_scanned_file(
            project_path=manifest.project_path,
            scanned_file=scanned_file,
            max_source_bytes=(
                max_source_bytes
            ),
        )
        for scanned_file in manifest.files
    )
