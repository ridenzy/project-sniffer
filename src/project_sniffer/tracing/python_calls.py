from __future__ import annotations

import symtable

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
    DynamicCallKind,
)
from project_sniffer.tracing.models import (
    CallResolution,
    CallResolutionStatus,
    CallResolutionProof,
    CallShadowReason,
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

def _confirmed_import_target(
    *,
    root: symtable.SymbolTable | None,
    target_name: str,
    ordered_candidates: tuple[
        CallTarget,
        ...,
    ],
    imported_bindings: Sequence[
        tuple[
            ImportResolution,
            CallTarget,
        ]
    ],
) -> tuple[
    CallTarget | None,
    CallResolutionProof | None,
]:
    if len(
        ordered_candidates
    ) != 1:
        return None, None

    target = ordered_candidates[0]

    matching_bindings = tuple(
        (
            resolution,
            candidate,
        )
        for (
            resolution,
            candidate,
        )
        in imported_bindings
        if candidate == target
    )

    if len(
        matching_bindings
    ) != 1:
        return None, None

    resolution, _ = (
        matching_bindings[0]
    )

    symbol = _binding_symbol(
        root,
        resolution.evidence.scope,
        target_name,
    )

    if symbol is None:
        return None, None

    if not symbol.is_imported():
        return None, None

    if (
        symbol.is_assigned()
        or symbol.is_parameter()
        or symbol.is_nonlocal()
        or symbol.is_free()
    ):
        return None, None

    return (
        target,
        (
            CallResolutionProof
            .INTERNAL_IMPORT_BINDING
        ),
    )

def _symbol_tables_by_path(
    index: SemanticProjectIndex,
) -> dict[
    str,
    symtable.SymbolTable,
]:
    tables: dict[
        str,
        symtable.SymbolTable,
    ] = {}

    for parsed in index.parsed_sources:
        if (
            parsed.source.language
            is not SourceLanguage.PYTHON
        ):
            continue

        content = (
            parsed
            .source
            .read_result
            .content
        )

        if content is None:
            continue

        source_path = (
            parsed
            .source
            .read_result
            .scanned_file
            .relative_path
        )

        try:
            tables[source_path] = (
                symtable.symtable(
                    content,
                    source_path,
                    "exec",
                )
            )
        except SyntaxError:
            continue

    return tables


def _scope_table(
    root: symtable.SymbolTable | None,
    scope: str | None,
) -> symtable.SymbolTable | None:
    if (
        root is None
        or scope is None
    ):
        return None

    current = root

    for part in scope.split(
        "."
    ):
        try:
            symbol = current.lookup(
                part
            )

            current = (
                symbol.get_namespace()
            )

        except (
            KeyError,
            ValueError,
        ):
            return None

    return current


def _scope_symbol(
    root: symtable.SymbolTable | None,
    scope: str | None,
    name: str,
) -> symtable.Symbol | None:
    table = _scope_table(
        root,
        scope,
    )

    if table is None:
        return None

    try:
        return table.lookup(
            name
        )

    except KeyError:
        return None

def _binding_symbol(
    root: symtable.SymbolTable | None,
    binding_scope: str | None,
    name: str,
) -> symtable.Symbol | None:
    if root is None:
        return None

    if binding_scope is None:
        table = root
    else:
        table = _scope_table(
            root,
            binding_scope,
        )

    if table is None:
        return None

    try:
        return table.lookup(
            name
        )

    except KeyError:
        return None

def _shadow_reason(
    symbol: symtable.Symbol | None,
    *,
    has_internal_import_candidate: bool,
) -> CallShadowReason | None:
    if symbol is None:
        return None

    if symbol.is_parameter():
        return (
            CallShadowReason.PARAMETER
        )

    if symbol.is_nonlocal():
        return (
            CallShadowReason.NONLOCAL
        )

    if symbol.is_free():
        return (
            CallShadowReason.FREE
        )

    if symbol.is_assigned():
        return (
            CallShadowReason.ASSIGNMENT
        )

    if symbol.is_imported():
        if has_internal_import_candidate:
            return None

        return (
            CallShadowReason.IMPORT
        )

    if symbol.is_local():
        return (
            CallShadowReason.LOCAL
        )

    return None

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

    symbol_tables = (
        _symbol_tables_by_path(
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
                    dynamic_kind=(
                        evidence.dynamic_kind
                        or DynamicCallKind.OTHER
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

        same_file_candidates: list[
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

        imported_candidates: list[
            CallTarget
        ] = []

        imported_bindings: list[
            tuple[
                ImportResolution,
                CallTarget,
            ]
        ] = []

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

            matching_targets = (
                symbols.get(
                    (
                        import_resolution
                        .target_path,
                        imported_name,
                    ),
                    (),
                )
            )

            imported_candidates.extend(
                matching_targets
            )

            imported_bindings.extend(
                (
                    import_resolution,
                    target,
                )
                for target
                in matching_targets
            )

        scope_symbol = (
            _scope_symbol(
                symbol_tables.get(
                    source_path
                ),
                evidence.scope,
                target_name,
            )
        )

        if (
            scope_symbol is not None
            and scope_symbol.is_parameter()
            and not same_file_candidates
            and not imported_candidates
        ):
            resolutions.append(
                CallResolution(
                    source_path=source_path,
                    evidence=evidence,
                    status=(
                        CallResolutionStatus
                        .DYNAMIC
                    ),
                    dynamic_kind=(
                        DynamicCallKind
                        .CALLBACK_PARAMETER
                    ),
                )
            )

            continue

        shadowed_by = (
            _shadow_reason(
                scope_symbol,
                has_internal_import_candidate=bool(
                    imported_candidates
                ),
            )
        )

        if shadowed_by is not None:
            resolutions.append(
                CallResolution(
                    source_path=source_path,
                    evidence=evidence,
                    status=(
                        CallResolutionStatus
                        .SHADOWED
                    ),
                    candidate_targets=(),
                    shadowed_by=shadowed_by,
                )
            )

            continue

        if (
            scope_symbol is not None
            and scope_symbol.is_imported()
            and imported_candidates
        ):
            candidates = (
                imported_candidates
            )

        else:
            candidates = [
                *same_file_candidates,
                *imported_candidates,
            ]

        ordered_candidates = (
            _ordered_unique_targets(
                candidates
            )
        )

        resolved_target, proof = (
            _confirmed_import_target(
                root=(
                    symbol_tables.get(
                        source_path
                    )
                ),
                target_name=target_name,
                ordered_candidates=(
                    ordered_candidates
                ),
                imported_bindings=(
                    imported_bindings
                ),
            )
        )

        if resolved_target is not None:
            status = (
                CallResolutionStatus
                .RESOLVED_INTERNAL
            )

        elif not ordered_candidates:
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
                resolved_target=resolved_target,
                proof=proof,
            )
        )

    return tuple(
        resolutions
    )
