from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from project_sniffer.scanning import (
    ScanManifest,
    ScannedFile,
)


_PUBLIC_DOCS_PREFIX = (
    "docs",
    "public",
)

_COPY_CHUNK_SIZE = 1024 * 1024


class DocsExportError(RuntimeError):
    """Raised when public documentation cannot be copied safely."""


@dataclass(frozen=True)
class DocsExportSummary:
    copied_files: int
    skipped_symlink_files: int
    skipped_unsafe_files: int
    skipped_unreadable_files: int


def _is_within(
    path: Path,
    root: Path,
) -> bool:
    try:
        path.relative_to(
            root
        )
    except ValueError:
        return False

    return True


def _public_docs_suffix(
    relative_path: str,
) -> PurePosixPath | None:
    path = PurePosixPath(
        relative_path
    )

    if (
        len(
            path.parts
        )
        < 3
        or path.parts[:2]
        != _PUBLIC_DOCS_PREFIX
    ):
        return None

    return PurePosixPath(
        *path.parts[2:]
    )


def _validated_source(
    *,
    project_root: Path,
    scanned_file: ScannedFile,
) -> tuple[Path | None, str | None]:
    candidate = Path(
        os.path.abspath(
            os.fspath(
                scanned_file.absolute_path
            )
        )
    )

    try:
        lexical_relative = (
            candidate.relative_to(
                project_root
            )
        )
    except ValueError:
        return None, "unsafe"

    if (
        lexical_relative.as_posix()
        != scanned_file.relative_path
    ):
        return None, "unsafe"

    if candidate.is_symlink():
        return None, "symlink"

    try:
        resolved = candidate.resolve(
            strict=True
        )
    except OSError:
        return None, "unreadable"

    if not _is_within(
        resolved,
        project_root,
    ):
        return None, "unsafe"

    try:
        source_stat = resolved.stat()
    except OSError:
        return None, "unreadable"

    if not stat.S_ISREG(
        source_stat.st_mode
    ):
        return None, "unreadable"

    return resolved, None


def _prepare_destination_parent(
    *,
    output_root: Path,
    suffix: PurePosixPath,
) -> Path:
    current = output_root

    for part in (
        "docs",
        "public",
        *suffix.parent.parts,
    ):
        candidate = (
            current
            / part
        )

        if candidate.is_symlink():
            raise DocsExportError(
                "documentation output path contains "
                f"a symlink: {candidate}"
            )

        if candidate.exists():
            if not candidate.is_dir():
                raise DocsExportError(
                    "documentation output path is not "
                    f"a directory: {candidate}"
                )
        else:
            try:
                candidate.mkdir()
            except OSError as error:
                raise DocsExportError(
                    "could not create documentation "
                    "output directory "
                    f"{candidate}: {error}"
                ) from error

        resolved = candidate.resolve(
            strict=True
        )

        if not _is_within(
            resolved,
            output_root,
        ):
            raise DocsExportError(
                "documentation output path escaped "
                f"its root: {candidate}"
            )

        current = resolved

    return current


def _copy_file(
    *,
    source: Path,
    destination: Path,
) -> None:
    temporary_path: Path | None = None

    try:
        source_flags = os.O_RDONLY

        if hasattr(
            os,
            "O_NOFOLLOW",
        ):
            source_flags |= os.O_NOFOLLOW

        source_fd = os.open(
            source,
            source_flags,
        )

        with os.fdopen(
            source_fd,
            "rb",
        ) as source_handle:
            source_stat = os.fstat(
                source_handle.fileno()
            )

            if not stat.S_ISREG(
                source_stat.st_mode
            ):
                raise DocsExportError(
                    "documentation source is not "
                    f"a regular file: {source}"
                )

            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=(
                    f".{destination.name}."
                ),
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(
                    temporary.name
                )

                while True:
                    chunk = source_handle.read(
                        _COPY_CHUNK_SIZE
                    )

                    if not chunk:
                        break

                    temporary.write(
                        chunk
                    )

        os.replace(
            temporary_path,
            destination,
        )

        temporary_path = None

    except DocsExportError:
        raise

    except OSError as error:
        raise DocsExportError(
            "could not copy documentation file "
            f"{source} -> {destination}: {error}"
        ) from error

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            try:
                temporary_path.unlink()
            except OSError:
                pass


def export_public_docs(
    *,
    manifest: ScanManifest,
    output_directory: Path,
) -> DocsExportSummary:
    """
    Copy manifest-approved root-level docs/public files.

    No discovery walk occurs here. Ignore policy remains
    authoritative because only canonical ScanManifest entries
    are considered.
    """

    project_root = (
        manifest.project_path
        .expanduser()
        .resolve()
    )

    output_root = (
        output_directory
        .expanduser()
        .resolve(
            strict=True
        )
    )

    copied_files = 0
    skipped_symlink_files = 0
    skipped_unsafe_files = 0
    skipped_unreadable_files = 0

    for scanned_file in manifest.files:
        suffix = _public_docs_suffix(
            scanned_file.relative_path
        )

        if suffix is None:
            continue

        source, reason = _validated_source(
            project_root=project_root,
            scanned_file=scanned_file,
        )

        if reason == "symlink":
            skipped_symlink_files += 1

            print(
                "[DOCS SKIP symlink] "
                f"{scanned_file.relative_path}"
            )

            continue

        if reason == "unsafe":
            skipped_unsafe_files += 1

            print(
                "[DOCS SKIP unsafe-path] "
                f"{scanned_file.relative_path}"
            )

            continue

        if (
            reason == "unreadable"
            or source is None
        ):
            skipped_unreadable_files += 1

            print(
                "[DOCS SKIP unreadable] "
                f"{scanned_file.relative_path}"
            )

            continue

        destination_parent = (
            _prepare_destination_parent(
                output_root=output_root,
                suffix=suffix,
            )
        )

        destination = (
            destination_parent
            / suffix.name
        )

        if destination.is_symlink():
            raise DocsExportError(
                "documentation output file is "
                f"a symlink: {destination}"
            )

        if (
            destination.exists()
            and not destination.is_file()
        ):
            raise DocsExportError(
                "documentation output file path is "
                f"not a regular file: {destination}"
            )

        _copy_file(
            source=source,
            destination=destination,
        )

        copied_files += 1

        print(
            "[DOCS COPY] "
            f"{scanned_file.relative_path}"
        )

    return DocsExportSummary(
        copied_files=copied_files,
        skipped_symlink_files=(
            skipped_symlink_files
        ),
        skipped_unsafe_files=(
            skipped_unsafe_files
        ),
        skipped_unreadable_files=(
            skipped_unreadable_files
        ),
    )
