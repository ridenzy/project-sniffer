from __future__ import annotations

import ast
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
    SymbolKind,
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
    call_scope: str | None,
    call_line: int,
    call_executes_during_module_initialization: bool,
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

    binding_scope = (
        resolution.evidence.scope
    )

    binding_must_precede_call = (
        binding_scope == call_scope
        or (
            binding_scope is None
            and (
                call_executes_during_module_initialization
            )
        )
    )

    if (
        binding_must_precede_call
        and resolution.evidence.line
        >= call_line
    ):
        return None, None

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

def _python_syntax_trees_by_path(
    index: SemanticProjectIndex,
) -> dict[str, ast.Module]:
    """
    Build Python ASTs from source text already held in memory.

    This performs no filesystem reads and does not execute target code.
    """

    trees: dict[
        str,
        ast.Module,
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
            trees[source_path] = (
                ast.parse(
                    content,
                    filename=source_path,
                    type_comments=True,
                )
            )

        except SyntaxError:
            continue

    return trees

def _ast_parent_map(
    tree: ast.AST,
) -> dict[
    ast.AST,
    ast.AST,
]:
    return {
        child: parent
        for parent in ast.walk(
            tree
        )
        for child in ast.iter_child_nodes(
            parent
        )
    }

def _call_executes_during_module_initialization(
    *,
    tree: ast.Module | None,
    target_name: str,
    call_line: int,
) -> bool:
    """
    Return True when a matching call is evaluated during module/class
    definition execution rather than from a deferred function or lambda body.

    This is deliberately not whole-program call-flow analysis. Calls inside
    function and lambda bodies are treated as deferred because their invocation
    timing is not proven at this stage.
    """

    if tree is None:
        return False

    parent_by_child = (
        _ast_parent_map(
            tree
        )
    )

    for node in ast.walk(
        tree
    ):
        if (
            not isinstance(
                node,
                ast.Call,
            )
            or node.lineno != call_line
            or not isinstance(
                node.func,
                ast.Name,
            )
            or node.func.id != target_name
        ):
            continue

        child: ast.AST = node
        parent = parent_by_child.get(
            node
        )
        deferred = False

        while parent is not None:
            if isinstance(
                parent,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                if any(
                    child is statement
                    for statement in parent.body
                ):
                    deferred = True
                    break

            if (
                isinstance(
                    parent,
                    ast.Lambda,
                )
                and child is parent.body
            ):
                deferred = True
                break

            child = parent
            parent = parent_by_child.get(
                parent
            )

        if not deferred:
            return True

    return False

def _lambda_binds_name(
    node: ast.Lambda,
    name: str,
) -> bool:
    arguments = node.args

    for argument in (
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
    ):
        if argument.arg == name:
            return True

    if (
        arguments.vararg is not None
        and arguments.vararg.arg == name
    ):
        return True

    if (
        arguments.kwarg is not None
        and arguments.kwarg.arg == name
    ):
        return True

    return False


def _comprehension_binds_name(
    node: (
        ast.ListComp
        | ast.SetComp
        | ast.DictComp
        | ast.GeneratorExp
    ),
    name: str,
) -> bool:
    for generator in node.generators:
        for target in ast.walk(
            generator.target
        ):
            if (
                isinstance(
                    target,
                    ast.Name,
                )
                and target.id == name
                and isinstance(
                    target.ctx,
                    ast.Store,
                )
            ):
                return True

    return False


def _call_has_unmodeled_scope_shadow(
    *,
    tree: ast.Module | None,
    target_name: str,
    call_line: int,
) -> bool:
    """
    Conservatively block positive call proof when the matching call is nested
    under a lambda or comprehension binding that CallEvidence.scope does not
    currently represent.
    """

    if tree is None:
        return False

    parent_by_child = (
        _ast_parent_map(
            tree
        )
    )

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if node.lineno != call_line:
            continue

        if (
            not isinstance(
                node.func,
                ast.Name,
            )
            or node.func.id != target_name
        ):
            continue

        parent = parent_by_child.get(
            node
        )

        while parent is not None:
            if (
                isinstance(
                    parent,
                    ast.Lambda,
                )
                and _lambda_binds_name(
                    parent,
                    target_name,
                )
            ):
                return True

            if (
                isinstance(
                    parent,
                    (
                        ast.ListComp,
                        ast.SetComp,
                        ast.DictComp,
                        ast.GeneratorExp,
                    ),
                )
                and _comprehension_binds_name(
                    parent,
                    target_name,
                )
            ):
                return True

            parent = parent_by_child.get(
                parent
            )

    return False


def _executes_in_module_scope(
    node: ast.AST,
    parent_by_child: dict[
        ast.AST,
        ast.AST,
    ],
) -> bool:
    parent = parent_by_child.get(
        node
    )

    while parent is not None:
        if isinstance(
            parent,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.Lambda,
                ast.ClassDef,
            ),
        ):
            return False

        if isinstance(
            parent,
            ast.Module,
        ):
            return True

        parent = parent_by_child.get(
            parent
        )

    return False


def _module_binding_sites(
    tree: ast.Module,
    name: str,
) -> tuple[
    tuple[str, int],
    ...,
]:
    """
    Find direct syntactic bindings that can affect a module name.

    Nested function/class-local bindings are ignored. Assignment expressions
    are treated conservatively wherever they occur.
    """

    parent_by_child = (
        _ast_parent_map(
            tree
        )
    )

    sites: list[
        tuple[str, int]
    ] = []

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.NamedExpr,
            )
            and isinstance(
                node.target,
                ast.Name,
            )
            and node.target.id == name
        ):
            sites.append(
                (
                    "named_expression",
                    node.lineno,
                )
            )

            continue

        if not _executes_in_module_scope(
            node,
            parent_by_child,
        ):
            continue

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            if node.name == name:
                sites.append(
                    (
                        "definition",
                        node.lineno,
                    )
                )

            continue

        if isinstance(
            node,
            ast.Import,
        ):
            for alias in node.names:
                bound_name = (
                    alias.asname
                    or alias.name.split(
                        "."
                    )[0]
                )

                if bound_name == name:
                    sites.append(
                        (
                            "import",
                            node.lineno,
                        )
                    )

            continue

        if isinstance(
            node,
            ast.ImportFrom,
        ):
            for alias in node.names:
                if alias.name == "*":
                    sites.append(
                        (
                            "star_import",
                            node.lineno,
                        )
                    )

                    continue

                bound_name = (
                    alias.asname
                    or alias.name
                )

                if bound_name == name:
                    sites.append(
                        (
                            "import",
                            node.lineno,
                        )
                    )

            continue

        if (
            isinstance(
                node,
                ast.Name,
            )
            and node.id == name
            and isinstance(
                node.ctx,
                (
                    ast.Store,
                    ast.Del,
                ),
            )
        ):
            sites.append(
                (
                    "name_binding",
                    node.lineno,
                )
            )

            continue

        if (
            isinstance(
                node,
                ast.ExceptHandler,
            )
            and node.name == name
        ):
            sites.append(
                (
                    "exception_binding",
                    node.lineno,
                )
            )

            continue

        if (
            isinstance(
                node,
                ast.MatchAs,
            )
            and node.name == name
        ):
            sites.append(
                (
                    "match_binding",
                    node.lineno,
                )
            )

            continue

        if (
            isinstance(
                node,
                ast.MatchStar,
            )
            and node.name == name
        ):
            sites.append(
                (
                    "match_binding",
                    node.lineno,
                )
            )

            continue

        if (
            isinstance(
                node,
                ast.MatchMapping,
            )
            and node.rest == name
        ):
            sites.append(
                (
                    "match_binding",
                    node.lineno,
                )
            )

    return tuple(
        sites
    )


def _definition_matches_target(
    node: ast.stmt,
    target: CallTarget,
) -> bool:
    if (
        getattr(
            node,
            "lineno",
            None,
        )
        != target.line
    ):
        return False

    if isinstance(
        node,
        ast.FunctionDef,
    ):
        return (
            node.name
            == target.qualified_name
            and target.kind
            is SymbolKind.FUNCTION
        )

    if isinstance(
        node,
        ast.AsyncFunctionDef,
    ):
        return (
            node.name
            == target.qualified_name
            and target.kind
            is SymbolKind.ASYNC_FUNCTION
        )

    if isinstance(
        node,
        ast.ClassDef,
    ):
        return (
            node.name
            == target.qualified_name
            and target.kind
            is SymbolKind.CLASS
        )

    return False


def _confirmed_same_file_target(
    *,
    tree: ast.Module | None,
    target_name: str,
    call_line: int,
    call_executes_during_module_initialization: bool,
    ordered_candidates: tuple[
        CallTarget,
        ...,
    ],
    same_file_candidates: Sequence[
        CallTarget
    ],
) -> tuple[
    CallTarget | None,
    CallResolutionProof | None,
]:
    if (
        tree is None
        or len(
            ordered_candidates
        ) != 1
    ):
        return None, None

    target = ordered_candidates[0]

    matching_same_file_targets = tuple(
        candidate
        for candidate
        in same_file_candidates
        if candidate == target
    )

    if len(
        matching_same_file_targets
    ) != 1:
        return None, None

    if (
        call_executes_during_module_initialization
        and target.line >= call_line
    ):
        return None, None

    definition = next(
        (
            node
            for node in tree.body
            if _definition_matches_target(
                node,
                target,
            )
        ),
        None,
    )

    if definition is None:
        return None, None

    if definition.decorator_list:
        return None, None

    binding_sites = (
        _module_binding_sites(
            tree,
            target_name,
        )
    )

    if binding_sites != (
        (
            "definition",
            target.line,
        ),
    ):
        return None, None

    return (
        target,
        (
            CallResolutionProof
            .SAME_FILE_STABLE_BINDING
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

    syntax_trees = (
        _python_syntax_trees_by_path(
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

        call_executes_during_module_initialization = (
            _call_executes_during_module_initialization(
                tree=syntax_trees.get(
                    source_path
                ),
                target_name=target_name,
                call_line=evidence.line,
            )
        )

        unmodeled_scope_shadow = (
            _call_has_unmodeled_scope_shadow(
                tree=syntax_trees.get(
                    source_path
                ),
                target_name=target_name,
                call_line=evidence.line,
            )
        )

        if unmodeled_scope_shadow:
            resolved_target = None
            proof = None

        else:
            resolved_target, proof = (
                _confirmed_import_target(
                    root=(
                        symbol_tables.get(
                            source_path
                        )
                    ),
                    target_name=target_name,
                    call_scope=evidence.scope,
                    call_line=evidence.line,
                    call_executes_during_module_initialization=(
                        call_executes_during_module_initialization
                    ),
                    ordered_candidates=(
                        ordered_candidates
                    ),
                    imported_bindings=(
                        imported_bindings
                    ),
                )
            )

            if resolved_target is None:
                resolved_target, proof = (
                    _confirmed_same_file_target(
                        tree=syntax_trees.get(
                            source_path
                        ),
                        target_name=target_name,
                        call_line=evidence.line,
                        call_executes_during_module_initialization=(
                            call_executes_during_module_initialization
                        ),
                        ordered_candidates=(
                            ordered_candidates
                        ),
                        same_file_candidates=(
                            same_file_candidates
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
