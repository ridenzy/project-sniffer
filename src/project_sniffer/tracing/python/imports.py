from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from project_sniffer.evidence import (
    SourceLanguage,
)
from project_sniffer.indexing import (
    SemanticProjectIndex,
)
from project_sniffer.parsing import (
    ImportEvidence,
)
from project_sniffer.tracing.models import (
    ImportResolution,
    ImportResolutionStatus,
)

def _module_aliases(
    relative_path: str,
) -> tuple[str, ...]:
    path = PurePosixPath(
        relative_path
    )

    if path.suffix.casefold() != ".py":
        return ()

    if path.name.casefold() == "__init__.py":
        module_parts = list(
            path.parts[:-1]
        )
    else:
        module_parts = [
            *path.parts[:-1],
            path.stem,
        ]

    if (
        len(module_parts) > 1
        and module_parts[0] == "src"
    ):
        module_parts = module_parts[1:]

    if not module_parts:
        return ()

    module_name = ".".join(
        module_parts
    )

    return (
        module_name,
    )


def _package_aliases(
    relative_path: str,
) -> tuple[str, ...]:
    path = PurePosixPath(
        relative_path
    )

    aliases = _module_aliases(
        relative_path
    )

    packages: list[str] = []

    for alias in aliases:
        if (
            path.name.casefold()
            == "__init__.py"
        ):
            package = alias
        elif "." in alias:
            package = alias.rsplit(
                ".",
                1,
            )[0]
        else:
            package = ""

        if (
            package
            and package not in packages
        ):
            packages.append(
                package
            )

    return tuple(
        packages
    )


def _requested_modules(
    source_path: str,
    evidence: ImportEvidence,
) -> tuple[
    tuple[str, ...],
    bool,
]:
    if evidence.level == 0:
        if evidence.module is None:
            return (), False

        return (
            (
                evidence.module,
            ),
            False,
        )

    packages = _package_aliases(
        source_path
    )

    if not packages:
        return (), True

    requested: list[str] = []

    upward_steps = (
        evidence.level
        - 1
    )

    for package in packages:
        package_parts = package.split(
            "."
        )

        if upward_steps >= len(
            package_parts
        ):
            continue

        if upward_steps:
            base_parts = package_parts[
                :-upward_steps
            ]
        else:
            base_parts = package_parts

        suffix_parts: list[str] = []

        if evidence.module:
            suffix_parts.extend(
                evidence.module.split(
                    "."
                )
            )
        elif evidence.imported_name:
            suffix_parts.append(
                evidence.imported_name
            )

        module_parts = [
            *base_parts,
            *suffix_parts,
        ]

        if not module_parts:
            continue

        module_name = ".".join(
            module_parts
        )

        if module_name not in requested:
            requested.append(
                module_name
            )

    if not requested:
        return (), True

    return (
        tuple(
            requested
        ),
        False,
    )


def _build_module_index(
    index: SemanticProjectIndex,
) -> dict[
    str,
    tuple[str, ...],
]:
    paths_by_module: dict[
        str,
        set[str],
    ] = defaultdict(
        set
    )

    for parsed in index.parsed_sources:
        if (
            parsed.source.language
            is not SourceLanguage.PYTHON
        ):
            continue

        source_path = (
            parsed
            .source
            .read_result
            .scanned_file
            .relative_path
        )

        for alias in _module_aliases(
            source_path
        ):
            paths_by_module[
                alias
            ].add(
                source_path
            )

    return {
        module: tuple(
            sorted(
                paths
            )
        )
        for module, paths
        in paths_by_module.items()
    }


def resolve_python_imports(
    index: SemanticProjectIndex,
) -> tuple[
    ImportResolution,
    ...,
]:
    module_index = (
        _build_module_index(
            index
        )
    )

    language_by_path = {
        (
            parsed
            .source
            .read_result
            .scanned_file
            .relative_path
        ): parsed.source.language
        for parsed
        in index.parsed_sources
    }

    resolutions: list[
        ImportResolution
    ] = []

    for indexed_import in index.imports:
        source_path = (
            indexed_import.source_path
        )

        if (
            language_by_path.get(
                source_path
            )
            is not SourceLanguage.PYTHON
        ):
            continue

        requested_modules, invalid = (
            _requested_modules(
                source_path,
                indexed_import.evidence,
            )
        )

        if invalid:
            resolutions.append(
                ImportResolution(
                    source_path=source_path,
                    evidence=(
                        indexed_import.evidence
                    ),
                    requested_modules=(),
                    status=(
                        ImportResolutionStatus
                        .INVALID_RELATIVE_IMPORT
                    ),
                )
            )

            continue

        candidate_paths: set[str] = set()

        for module in requested_modules:
            candidate_paths.update(
                module_index.get(
                    module,
                    (),
                )
            )

        ordered_candidates = tuple(
            sorted(
                candidate_paths
            )
        )

        if not ordered_candidates:
            status = (
                ImportResolutionStatus
                .UNRESOLVED
            )

            target_path = None

        elif len(
            ordered_candidates
        ) == 1:
            status = (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            )

            target_path = (
                ordered_candidates[0]
            )

        else:
            status = (
                ImportResolutionStatus
                .AMBIGUOUS
            )

            target_path = None

        resolutions.append(
            ImportResolution(
                source_path=source_path,
                evidence=(
                    indexed_import.evidence
                ),
                requested_modules=(
                    requested_modules
                ),
                status=status,
                target_path=target_path,
                candidate_paths=(
                    ordered_candidates
                ),
            )
        )

    return tuple(
        resolutions
    )
