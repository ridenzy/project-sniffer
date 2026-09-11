from __future__ import annotations

from collections.abc import Sequence

from project_sniffer.evidence import (
    SourceLanguage,
)
from project_sniffer.indexing import (
    IndexedSymbol,
    SemanticProjectIndex,
)
from project_sniffer.parsing import (
    CallTargetKind,
)
from project_sniffer.tracing.models import (
    CallResolution,
    CallResolutionStatus,
    CallTarget,
    ImportResolution,
    ImportResolutionStatus,
)


def _language_by_path(
    index: SemanticProjectIndex,
) -> dict[str, SourceLanguage]:
    return {
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


def _top_level_target(
    symbol: IndexedSymbol,
) -> CallTarget | None:
    evidence = symbol.evidence

    if (
        evidence.qualified_name
        != evidence.name
    ):
        return None

    return CallTarget(
        source_path=symbol.source_path,
        qualified_name=(
            evidence.qualified_name
        ),
        kind=evidence.kind,
        line=evidence.line,
    )


def _build_top_level_symbol_index(
    index: SemanticProjectIndex,
) -> dict[
    tuple[str, str],
    tuple[CallTarget, ...],
]:
    targets: dict[
        tuple[str, str],
        list[CallTarget],
    ] = {}

    for symbol in index.symbols:
        target = _top_level_target(
            symbol
        )

        if target is None:
            continue

        key = (
            symbol.source_path,
            symbol.evidence.name,
        )

        targets.setdefault(
            key,
            [],
        ).append(
            target
        )

    return {
        key: tuple(
            sorted(
                values,
                key=lambda item: (
                    item.source_path,
                    item.line,
                    item.qualified_name,
                    item.kind.value,
                ),
            )
        )
        for key, values
        in targets.items()
    }


def _binding_is_visible(
    binding_scope: str | None,
    call_scope: str | None,
) -> bool:
    if binding_scope is None:
        return True

    if call_scope is None:
        return False

    return (
        call_scope == binding_scope
        or call_scope.startswith(
            f"{binding_scope}."
        )
    )


def _import_bound_name(
    resolution: ImportResolution,
) -> str | None:
    evidence = resolution.evidence

    if evidence.imported_name is None:
        return None

    return (
        evidence.alias
        or evidence.imported_name
    )


def _ordered_unique_targets(
    targets: Sequence[CallTarget],
) -> tuple[CallTarget, ...]:
    unique = {
        (
            target.source_path,
            target.qualified_name,
            target.kind,
            target.line,
        ): target
        for target in targets
    }

    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                item.source_path,
                item.line,
                item.qualified_name,
                item.kind.value,
            ),
        )
    )


def resolve_python_calls(
    index: SemanticProjectIndex,
    import_resolutions: Sequence[
        ImportResolution
    ],
) -> tuple[
    CallResolution,
    ...,
]:
    language_by_path = (
        _language_by_path(
            index
        )
    )

    symbols = (
        _build_top_level_symbol_index(
            index
        )
    )

    resolutions: list[
        CallResolution
    ] = []

    for indexed_call in index.calls:
        source_path = (
            indexed_call.source_path
        )

        evidence = (
            indexed_call.evidence
        )

        if (
            language_by_path.get(
                source_path
            )
            is not SourceLanguage.PYTHON
        ):
            continue

        if (
            evidence.target_kind
            is CallTargetKind.DYNAMIC
        ):
            resolutions.append(
                CallResolution(
                    source_path=source_path,
                    evidence=evidence,
                    status=(
                        CallResolutionStatus
                        .DYNAMIC
                    ),
                )
            )

            continue

        if (
            evidence.target_kind
            is not CallTargetKind.NAME
            or len(
                evidence.target_parts
            ) != 1
        ):
            resolutions.append(
                CallResolution(
                    source_path=source_path,
                    evidence=evidence,
                    status=(
                        CallResolutionStatus
                        .UNRESOLVED
                    ),
                )
            )

            continue

        target_name = (
            evidence.target_parts[0]
        )

        candidates: list[
            CallTarget
        ] = list(
            symbols.get(
                (
                    source_path,
                    target_name,
                ),
                (),
            )
        )

        for import_resolution in (
            import_resolutions
        ):
            if (
                import_resolution.source_path
                != source_path
            ):
                continue

            if (
                import_resolution.status
                is not (
                    ImportResolutionStatus
                    .RESOLVED_INTERNAL
                )
            ):
                continue

            if (
                import_resolution.target_path
                is None
            ):
                continue

            if not _binding_is_visible(
                import_resolution
                .evidence
                .scope,
                evidence.scope,
            ):
                continue

            bound_name = (
                _import_bound_name(
                    import_resolution
                )
            )

            if bound_name != target_name:
                continue

            imported_name = (
                import_resolution
                .evidence
                .imported_name
            )

            if imported_name is None:
                continue

            candidates.extend(
                symbols.get(
                    (
                        import_resolution
                        .target_path,
                        imported_name,
                    ),
                    (),
                )
            )

        ordered_candidates = (
            _ordered_unique_targets(
                candidates
            )
        )

        if not ordered_candidates:
            status = (
                CallResolutionStatus
                .UNRESOLVED
            )

        elif len(
            ordered_candidates
        ) == 1:
            status = (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            )

        else:
            status = (
                CallResolutionStatus
                .AMBIGUOUS
            )

        resolutions.append(
            CallResolution(
                source_path=source_path,
                evidence=evidence,
                status=status,
                candidate_targets=(
                    ordered_candidates
                ),
            )
        )

    return tuple(
        resolutions
    )
