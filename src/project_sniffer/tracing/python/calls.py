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


def _build_qualified_symbol_index(
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
        evidence = symbol.evidence

        target = CallTarget(
            source_path=symbol.source_path,
            qualified_name=(
                evidence.qualified_name
            ),
            kind=evidence.kind,
            line=evidence.line,
        )

        key = (
            symbol.source_path,
            evidence.qualified_name,
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

def _module_import_bound_name(
    resolution: ImportResolution,
) -> str | None:
    evidence = resolution.evidence

    if (
        evidence.imported_name is not None
        or evidence.module is None
    ):
        return None

    if evidence.alias is not None:
        return evidence.alias

    if "." in evidence.module:
        return None

    return evidence.module

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

def _attribute_call_has_implicit_scope(
    *,
    tree: ast.Module | None,
    target_parts: tuple[str, ...],
    call_line: int,
) -> bool:
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
        ):
            continue

        parts: list[str] = []
        current: ast.AST = node.func

        while isinstance(
            current,
            ast.Attribute,
        ):
            parts.append(
                current.attr
            )
            current = current.value

        if not isinstance(
            current,
            ast.Name,
        ):
            continue

        parts.append(
            current.id
        )

        if tuple(
            reversed(
                parts
            )
        ) != target_parts:
            continue

        parent = parent_by_child.get(
            node
        )

        while parent is not None:
            if isinstance(
                parent,
                (
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                return True

            parent = parent_by_child.get(
                parent
            )

    return False

def _attribute_call_executes_during_module_initialization(
    *,
    tree: ast.Module | None,
    target_parts: tuple[str, ...],
    call_line: int,
) -> bool:
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
        ):
            continue

        parts: list[str] = []
        current: ast.AST = node.func

        while isinstance(
            current,
            ast.Attribute,
        ):
            parts.append(
                current.attr
            )
            current = current.value

        if not isinstance(
            current,
            ast.Name,
        ):
            continue

        parts.append(
            current.id
        )

        if tuple(
            reversed(
                parts
            )
        ) != target_parts:
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

def _find_direct_class_definition(
    *,
    tree: ast.Module | None,
    target: CallTarget,
) -> ast.ClassDef | None:
    if (
        tree is None
        or target.kind is not SymbolKind.CLASS
    ):
        return None

    for node in tree.body:
        if (
            isinstance(
                node,
                ast.ClassDef,
            )
            and _definition_matches_target(
                node,
                target,
            )
        ):
            return node

    return None

def _executes_in_class_scope(
    node: ast.AST,
    *,
    class_node: ast.ClassDef,
    parent_by_child: dict[
        ast.AST,
        ast.AST,
    ],
) -> bool:
    if node is class_node:
        return False

    parent = parent_by_child.get(
        node
    )

    while parent is not None:
        if parent is class_node:
            return True

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

        parent = parent_by_child.get(
            parent
        )

    return False

def _class_binding_sites(
    *,
    tree: ast.Module,
    class_node: ast.ClassDef,
    name: str,
) -> tuple[
    tuple[str, int],
    ...,
]:
    parent_by_child = (
        _ast_parent_map(
            tree
        )
    )

    sites: list[
        tuple[str, int]
    ] = []

    for node in ast.walk(
        class_node
    ):
        if not _executes_in_class_scope(
            node,
            class_node=class_node,
            parent_by_child=parent_by_child,
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

def _named_receiver_attribute_mutation_exists(
    *,
    tree: ast.Module | None,
    receiver_name: str,
    member_name: str,
) -> bool:
    if tree is None:
        return True

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.Attribute,
            )
            and node.attr == member_name
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id == receiver_name
            and isinstance(
                node.ctx,
                (
                    ast.Store,
                    ast.Del,
                ),
            )
        ):
            return True

        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id
            in {
                "setattr",
                "delattr",
            }
            and len(
                node.args
            ) >= 2
            and isinstance(
                node.args[0],
                ast.Name,
            )
            and node.args[0].id
            == receiver_name
            and isinstance(
                node.args[1],
                ast.Constant,
            )
            and node.args[1].value
            == member_name
        ):
            return True

    return False


def _confirmed_class_member_target(
    *,
    tree: ast.Module | None,
    class_target: CallTarget,
    member_target: CallTarget,
) -> CallTarget | None:
    if tree is None:
        return None

    class_node = (
        _find_direct_class_definition(
            tree=tree,
            target=class_target,
        )
    )

    if class_node is None:
        return None

    if (
        class_node.bases
        or class_node.keywords
    ):
        return None

    member_name = (
        member_target
        .qualified_name
        .rsplit(
            ".",
            1,
        )[-1]
    )

    expected_qualified_name = (
        f"{class_target.qualified_name}"
        f".{member_name}"
    )

    if (
        member_target.qualified_name
        != expected_qualified_name
        or member_target.kind
        not in {
            SymbolKind.FUNCTION,
            SymbolKind.ASYNC_FUNCTION,
        }
    ):
        return None

    definition = next(
        (
            node
            for node in class_node.body
            if (
                isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                )
                and node.name
                == member_name
                and node.lineno
                == member_target.line
            )
        ),
        None,
    )

    if (
        definition is None
        or definition.decorator_list
    ):
        return None

    binding_sites = (
        _class_binding_sites(
            tree=tree,
            class_node=class_node,
            name=member_name,
        )
    )

    if binding_sites != (
        (
            "definition",
            member_target.line,
        ),
    ):
        return None

    if _named_receiver_attribute_mutation_exists(
        tree=tree,
        receiver_name=(
            class_target.qualified_name
        ),
        member_name=member_name,
    ):
        return None

    return member_target


def _confirmed_module_attribute_target(
    *,
    root: symtable.SymbolTable | None,
    syntax_trees: dict[
        str,
        ast.Module,
    ],
    call_scope: str | None,
    call_line: int,
    receiver_name: str,
    candidates: tuple[
        CallTarget,
        ...,
    ],
    bindings: Sequence[
        tuple[
            ImportResolution,
            CallTarget,
        ]
    ],
) -> tuple[
    CallTarget | None,
    CallResolutionProof | None,
]:
    if len(candidates) != 1:
        return None, None

    target = candidates[0]

    matching_bindings = tuple(
        item
        for item in bindings
        if item[1] == target
    )

    if len(matching_bindings) != 1:
        return None, None

    resolution, _ = matching_bindings[0]
    binding_scope = resolution.evidence.scope

    if (
        binding_scope == call_scope
        and resolution.evidence.line
        >= call_line
    ):
        return None, None

    symbol = _binding_symbol(
        root,
        binding_scope,
        receiver_name,
    )

    if (
        symbol is None
        or not symbol.is_imported()
        or symbol.is_assigned()
        or symbol.is_parameter()
        or symbol.is_nonlocal()
        or symbol.is_free()
    ):
        return None, None

    stable_target, _ = (
        _confirmed_same_file_target(
            tree=syntax_trees.get(
                target.source_path
            ),
            target_name=(
                target.qualified_name
            ),
            call_line=0,
            call_executes_during_module_initialization=False,
            ordered_candidates=(target,),
            same_file_candidates=(target,),
        )
    )

    if stable_target is None:
        return None, None

    return (
        target,
        (
            CallResolutionProof
            .INTERNAL_MODULE_ATTRIBUTE_BINDING
        ),
    )

def _resolve_module_attribute_call(
    *,
    source_path: str,
    evidence,
    symbols: dict[
        tuple[str, str],
        tuple[CallTarget, ...],
    ],
    import_resolutions: Sequence[
        ImportResolution
    ],
    symbol_tables: dict[
        str,
        symtable.SymbolTable,
    ],
    syntax_trees: dict[
        str,
        ast.Module,
    ],
) -> CallResolution | None:
    if (
        len(evidence.target_parts) != 2
        or _attribute_call_has_implicit_scope(
            tree=syntax_trees.get(
                source_path
            ),
            target_parts=(
                evidence.target_parts
            ),
            call_line=evidence.line,
        )
    ):
        return None

    receiver_name, member_name = (
        evidence.target_parts
    )

    candidates: list[
        CallTarget
    ] = []

    bindings: list[
        tuple[
            ImportResolution,
            CallTarget,
        ]
    ] = []

    for resolution in import_resolutions:
        if (
            resolution.source_path
            != source_path
            or resolution.status
            is not (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            )
            or resolution.target_path
            is None
            or not _binding_is_visible(
                resolution.evidence.scope,
                evidence.scope,
            )
            or _module_import_bound_name(
                resolution
            )
            != receiver_name
        ):
            continue

        matching_targets = (
            symbols.get(
                (
                    resolution.target_path,
                    member_name,
                ),
                (),
            )
        )

        candidates.extend(
            matching_targets
        )

        bindings.extend(
            (
                resolution,
                target,
            )
            for target
            in matching_targets
        )

    ordered_candidates = (
        _ordered_unique_targets(
            candidates
        )
    )

    if not ordered_candidates:
        return None

    scope_symbol = _scope_symbol(
        symbol_tables.get(
            source_path
        ),
        evidence.scope,
        receiver_name,
    )

    shadowed_by = _shadow_reason(
        scope_symbol,
        has_internal_import_candidate=True,
    )

    if shadowed_by is not None:
        return CallResolution(
            source_path=source_path,
            evidence=evidence,
            status=(
                CallResolutionStatus
                .SHADOWED
            ),
            shadowed_by=shadowed_by,
        )

    caller_attribute_mutated = (
        _named_receiver_attribute_mutation_exists(
            tree=syntax_trees.get(
                source_path
            ),
            receiver_name=receiver_name,
            member_name=member_name,
        )
    )

    if caller_attribute_mutated:
        resolved_target = None
        proof = None
    else:
        resolved_target, proof = (
            _confirmed_module_attribute_target(
                root=symbol_tables.get(
                    source_path
                ),
                syntax_trees=syntax_trees,
                call_scope=evidence.scope,
                call_line=evidence.line,
                receiver_name=receiver_name,
                candidates=ordered_candidates,
                bindings=bindings,
            )
        )

    if resolved_target is not None:
        status = (
            CallResolutionStatus
            .RESOLVED_INTERNAL
        )

    elif len(ordered_candidates) == 1:
        status = (
            CallResolutionStatus
            .POTENTIAL_INTERNAL
        )

    else:
        status = (
            CallResolutionStatus
            .AMBIGUOUS
        )

    return CallResolution(
        source_path=source_path,
        evidence=evidence,
        status=status,
        candidate_targets=(
            ordered_candidates
        ),
        resolved_target=resolved_target,
        proof=proof,
    )

def _resolve_class_attribute_call(
    *,
    source_path: str,
    evidence,
    top_level_symbols: dict[
        tuple[str, str],
        tuple[CallTarget, ...],
    ],
    qualified_symbols: dict[
        tuple[str, str],
        tuple[CallTarget, ...],
    ],
    import_resolutions: Sequence[
        ImportResolution
    ],
    symbol_tables: dict[
        str,
        symtable.SymbolTable,
    ],
    syntax_trees: dict[
        str,
        ast.Module,
    ],
) -> CallResolution | None:
    if (
        len(evidence.target_parts) != 2
        or _attribute_call_has_implicit_scope(
            tree=syntax_trees.get(
                source_path
            ),
            target_parts=(
                evidence.target_parts
            ),
            call_line=evidence.line,
        )
    ):
        return None

    receiver_name, member_name = (
        evidence.target_parts
    )

    same_file_classes = tuple(
        target
        for target in top_level_symbols.get(
            (
                source_path,
                receiver_name,
            ),
            (),
        )
        if target.kind is SymbolKind.CLASS
    )

    imported_classes: list[
        CallTarget
    ] = []

    imported_bindings: list[
        tuple[
            ImportResolution,
            CallTarget,
        ]
    ] = []

    for resolution in import_resolutions:
        if (
            resolution.source_path
            != source_path
            or resolution.status
            is not (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            )
            or resolution.target_path
            is None
            or not _binding_is_visible(
                resolution.evidence.scope,
                evidence.scope,
            )
            or _import_bound_name(
                resolution
            )
            != receiver_name
            or resolution.evidence.imported_name
            is None
        ):
            continue

        matching_classes = tuple(
            target
            for target in top_level_symbols.get(
                (
                    resolution.target_path,
                    (
                        resolution
                        .evidence
                        .imported_name
                    ),
                ),
                (),
            )
            if target.kind
            is SymbolKind.CLASS
        )

        imported_classes.extend(
            matching_classes
        )

        imported_bindings.extend(
            (
                resolution,
                target,
            )
            for target
            in matching_classes
        )

    scope_symbol = _scope_symbol(
        symbol_tables.get(
            source_path
        ),
        evidence.scope,
        receiver_name,
    )

    if (
        scope_symbol is not None
        and scope_symbol.is_imported()
        and imported_classes
    ):
        class_candidates = (
            imported_classes
        )
    else:
        class_candidates = [
            *same_file_classes,
            *imported_classes,
        ]

    ordered_class_candidates = (
        _ordered_unique_targets(
            class_candidates
        )
    )

    if not ordered_class_candidates:
        return None

    shadowed_by = _shadow_reason(
        scope_symbol,
        has_internal_import_candidate=bool(
            imported_classes
        ),
    )

    if shadowed_by is not None:
        return CallResolution(
            source_path=source_path,
            evidence=evidence,
            status=(
                CallResolutionStatus
                .SHADOWED
            ),
            shadowed_by=shadowed_by,
        )

    call_executes_immediately = (
        _attribute_call_executes_during_module_initialization(
            tree=syntax_trees.get(
                source_path
            ),
            target_parts=(
                evidence.target_parts
            ),
            call_line=evidence.line,
        )
    )

    class_target, class_proof = (
        _confirmed_import_target(
            root=symbol_tables.get(
                source_path
            ),
            target_name=receiver_name,
            call_scope=evidence.scope,
            call_line=evidence.line,
            call_executes_during_module_initialization=(
                call_executes_immediately
            ),
            ordered_candidates=(
                ordered_class_candidates
            ),
            imported_bindings=(
                imported_bindings
            ),
        )
    )

    if class_target is None:
        class_target, class_proof = (
            _confirmed_same_file_target(
                tree=syntax_trees.get(
                    source_path
                ),
                target_name=receiver_name,
                call_line=evidence.line,
                call_executes_during_module_initialization=(
                    call_executes_immediately
                ),
                ordered_candidates=(
                    ordered_class_candidates
                ),
                same_file_candidates=(
                    same_file_classes
                ),
            )
        )

    if (
        class_target is not None
        and class_proof
        is (
            CallResolutionProof
            .SAME_FILE_STABLE_BINDING
        )
        and call_executes_immediately
        and evidence.scope is not None
        and (
            evidence.scope
            == class_target.qualified_name
            or evidence.scope.startswith(
                f"{class_target.qualified_name}."
            )
        )
    ):
        class_target = None
        class_proof = None

    member_candidates: list[
        CallTarget
    ] = []

    for candidate_class in (
        ordered_class_candidates
    ):
        member_candidates.extend(
            qualified_symbols.get(
                (
                    candidate_class.source_path,
                    (
                        f"{candidate_class.qualified_name}"
                        f".{member_name}"
                    ),
                ),
                (),
            )
        )

    ordered_member_candidates = (
        _ordered_unique_targets(
            member_candidates
        )
    )

    if not ordered_member_candidates:
        return None

    caller_attribute_mutated = (
        _named_receiver_attribute_mutation_exists(
            tree=syntax_trees.get(
                source_path
            ),
            receiver_name=receiver_name,
            member_name=member_name,
        )
    )

    resolved_target = None
    proof = None

    if (
        class_target is not None
        and not caller_attribute_mutated
        and len(
            ordered_member_candidates
        ) == 1
    ):
        target_tree = syntax_trees.get(
            class_target.source_path
        )

        stable_class_target, _ = (
            _confirmed_same_file_target(
                tree=target_tree,
                target_name=(
                    class_target
                    .qualified_name
                ),
                call_line=0,
                call_executes_during_module_initialization=False,
                ordered_candidates=(
                    class_target,
                ),
                same_file_candidates=(
                    class_target,
                ),
            )
        )

        member_target = (
            ordered_member_candidates[0]
        )

        if (
            stable_class_target
            is not None
            and member_target.source_path
            == class_target.source_path
            and member_target.qualified_name
            == (
                f"{class_target.qualified_name}"
                f".{member_name}"
            )
            and _confirmed_class_member_target(
                tree=target_tree,
                class_target=class_target,
                member_target=member_target,
            )
            is not None
        ):
            resolved_target = (
                member_target
            )

            if (
                class_proof
                is (
                    CallResolutionProof
                    .SAME_FILE_STABLE_BINDING
                )
            ):
                proof = (
                    CallResolutionProof
                    .SAME_FILE_CLASS_ATTRIBUTE_BINDING
                )

            elif (
                class_proof
                is (
                    CallResolutionProof
                    .INTERNAL_IMPORT_BINDING
                )
            ):
                proof = (
                    CallResolutionProof
                    .INTERNAL_IMPORTED_CLASS_ATTRIBUTE_BINDING
                )

    if (
        resolved_target is not None
        and proof is not None
    ):
        status = (
            CallResolutionStatus
            .RESOLVED_INTERNAL
        )

    elif len(
        ordered_member_candidates
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

    return CallResolution(
        source_path=source_path,
        evidence=evidence,
        status=status,
        candidate_targets=(
            ordered_member_candidates
        ),
        resolved_target=resolved_target,
        proof=proof,
    )

def _direct_function_scope_node(
    *,
    tree: ast.Module | None,
    scope: str | None,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    if (
        tree is None
        or scope is None
    ):
        return None

    scope_parts = tuple(
        scope.split(
            "."
        )
    )

    if len(scope_parts) == 1:
        container = tree.body
        function_name = scope_parts[0]

    elif len(scope_parts) == 2:
        class_name, function_name = (
            scope_parts
        )

        class_matches = tuple(
            node
            for node in tree.body
            if (
                isinstance(
                    node,
                    ast.ClassDef,
                )
                and node.name
                == class_name
            )
        )

        if len(class_matches) != 1:
            return None

        container = (
            class_matches[0].body
        )

    else:
        return None

    matches = tuple(
        node
        for node in container
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name
            == function_name
        )
    )

    if len(matches) != 1:
        return None

    return matches[0]


def _matching_attribute_call_node(
    *,
    tree: ast.Module,
    target_parts: tuple[str, ...],
    call_line: int,
) -> ast.Call | None:
    matches: list[ast.Call] = []

    for node in ast.walk(
        tree
    ):
        if (
            not isinstance(
                node,
                ast.Call,
            )
            or node.lineno != call_line
        ):
            continue

        parts: list[str] = []
        current: ast.AST = node.func

        while isinstance(
            current,
            ast.Attribute,
        ):
            parts.append(
                current.attr
            )
            current = current.value

        if not isinstance(
            current,
            ast.Name,
        ):
            continue

        parts.append(
            current.id
        )

        if tuple(
            reversed(
                parts
            )
        ) == target_parts:
            matches.append(
                node
            )

    if len(matches) != 1:
        return None

    return matches[0]


def _direct_function_statement(
    *,
    node: ast.AST,
    function_node: (
        ast.FunctionDef
        | ast.AsyncFunctionDef
    ),
    parent_by_child: dict[
        ast.AST,
        ast.AST,
    ],
) -> ast.stmt | None:
    child = node
    parent = parent_by_child.get(
        node
    )

    while parent is not None:
        if parent is function_node:
            return (
                child
                if isinstance(
                    child,
                    ast.stmt,
                )
                else None
            )

        if isinstance(
            parent,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.Lambda,
                ast.ClassDef,
                ast.ListComp,
                ast.SetComp,
                ast.DictComp,
                ast.GeneratorExp,
            ),
        ):
            return None

        child = parent
        parent = parent_by_child.get(
            parent
        )

    return None


def _statement_is_direct_call(
    *,
    statement: ast.stmt,
    call: ast.Call,
) -> bool:
    if isinstance(
        statement,
        ast.Expr,
    ):
        return statement.value is call

    if isinstance(
        statement,
        ast.Return,
    ):
        return statement.value is call

    if isinstance(
        statement,
        ast.Assign,
    ):
        return statement.value is call

    if isinstance(
        statement,
        ast.AnnAssign,
    ):
        return statement.value is call

    return False


def _passive_local_instance_gap_expression(
    node: ast.expr,
    *,
    receiver_name: str,
) -> bool:
    if isinstance(
        node,
        ast.Constant,
    ):
        return True

    if isinstance(
        node,
        ast.Name,
    ):
        return (
            isinstance(
                node.ctx,
                ast.Load,
            )
            and node.id
            != receiver_name
        )

    if isinstance(
        node,
        (
            ast.Tuple,
            ast.List,
        ),
    ):
        return all(
            _passive_local_instance_gap_expression(
                element,
                receiver_name=receiver_name,
            )
            for element in node.elts
        )

    return False


def _passive_local_instance_gap_statement(
    statement: ast.stmt,
    *,
    receiver_name: str,
) -> bool:
    if isinstance(
        statement,
        ast.Pass,
    ):
        return True

    if (
        isinstance(
            statement,
            ast.Expr,
        )
        and isinstance(
            statement.value,
            ast.Constant,
        )
    ):
        return True

    if not isinstance(
        statement,
        ast.Assign,
    ):
        return False

    if not statement.targets:
        return False

    if not all(
        isinstance(
            target,
            ast.Name,
        )
        and target.id
        != receiver_name
        for target in statement.targets
    ):
        return False

    return (
        _passive_local_instance_gap_expression(
            statement.value,
            receiver_name=receiver_name,
        )
    )


def _stable_local_constructor_assignment(
    *,
    function_node: (
        ast.FunctionDef
        | ast.AsyncFunctionDef
    ),
    method_index: int,
    receiver_name: str,
    call_line: int,
) -> ast.Assign | None:
    for statement in reversed(
        function_node.body[
            :method_index
        ]
    ):
        if (
            isinstance(
                statement,
                ast.Assign,
            )
            and len(
                statement.targets
            ) == 1
            and isinstance(
                statement.targets[0],
                ast.Name,
            )
            and statement.targets[0].id
            == receiver_name
            and isinstance(
                statement.value,
                ast.Call,
            )
            and isinstance(
                statement.value.func,
                ast.Name,
            )
            and not statement.value.args
            and not statement.value.keywords
            and statement.lineno
            < call_line
        ):
            return statement

        if not _passive_local_instance_gap_statement(
            statement,
            receiver_name=receiver_name,
        ):
            return None

    return None


def _class_allows_direct_instance_method_proof(
    *,
    tree: ast.Module | None,
    class_target: CallTarget,
) -> bool:
    class_node = (
        _find_direct_class_definition(
            tree=tree,
            target=class_target,
        )
    )

    if (
        tree is None
        or class_node is None
        or class_node.bases
        or class_node.keywords
    ):
        return False

    for name in (
        "__new__",
        "__init__",
        "__getattribute__",
    ):
        if _class_binding_sites(
            tree=tree,
            class_node=class_node,
            name=name,
        ):
            return False

    return True


def _resolve_local_instance_attribute_call(
    *,
    source_path: str,
    evidence,
    qualified_symbols: dict[
        tuple[str, str],
        tuple[CallTarget, ...],
    ],
    prior_resolutions: Sequence[
        CallResolution
    ],
    symbol_tables: dict[
        str,
        symtable.SymbolTable,
    ],
    syntax_trees: dict[
        str,
        ast.Module,
    ],
) -> CallResolution | None:
    if (
        len(evidence.target_parts) != 2
        or evidence.scope is None
    ):
        return None

    tree = syntax_trees.get(
        source_path
    )

    if tree is None:
        return None

    if _attribute_call_has_implicit_scope(
        tree=tree,
        target_parts=evidence.target_parts,
        call_line=evidence.line,
    ):
        return None

    function_node = (
        _direct_function_scope_node(
            tree=tree,
            scope=evidence.scope,
        )
    )

    method_call = (
        _matching_attribute_call_node(
            tree=tree,
            target_parts=evidence.target_parts,
            call_line=evidence.line,
        )
    )

    if (
        function_node is None
        or method_call is None
    ):
        return None

    parent_by_child = (
        _ast_parent_map(
            tree
        )
    )

    method_statement = (
        _direct_function_statement(
            node=method_call,
            function_node=function_node,
            parent_by_child=parent_by_child,
        )
    )

    if (
        method_statement is None
        or not _statement_is_direct_call(
            statement=method_statement,
            call=method_call,
        )
    ):
        return None

    method_index = next(
        (
            position
            for position, statement
            in enumerate(
                function_node.body
            )
            if statement is method_statement
        ),
        None,
    )

    if (
        method_index is None
        or method_index == 0
    ):
        return None

    receiver_name, member_name = (
        evidence.target_parts
    )

    assignment = (
        _stable_local_constructor_assignment(
            function_node=function_node,
            method_index=method_index,
            receiver_name=receiver_name,
            call_line=evidence.line,
        )
    )

    if assignment is None:
        return None

    receiver_symbol = _scope_symbol(
        symbol_tables.get(
            source_path
        ),
        evidence.scope,
        receiver_name,
    )

    if (
        receiver_symbol is None
        or not receiver_symbol.is_local()
        or not receiver_symbol.is_assigned()
        or receiver_symbol.is_parameter()
        or receiver_symbol.is_imported()
        or receiver_symbol.is_nonlocal()
        or receiver_symbol.is_free()
        or receiver_symbol.is_global()
    ):
        return None

    constructor_name = (
        assignment.value.func.id
    )

    constructor_resolutions = tuple(
        resolution
        for resolution in prior_resolutions
        if (
            resolution.source_path
            == source_path
            and resolution.evidence.scope
            == evidence.scope
            and resolution.evidence.line
            == assignment.value.lineno
            and resolution.evidence.target_kind
            is CallTargetKind.NAME
            and resolution.evidence.target_parts
            == (constructor_name,)
            and resolution.status
            is CallResolutionStatus.RESOLVED_INTERNAL
            and resolution.resolved_target
            is not None
            and resolution.resolved_target.kind
            is SymbolKind.CLASS
        )
    )

    if len(
        constructor_resolutions
    ) != 1:
        return None

    class_target = (
        constructor_resolutions[0]
        .resolved_target
    )

    target_tree = syntax_trees.get(
        class_target.source_path
    )

    stable_class_target, _ = (
        _confirmed_same_file_target(
            tree=target_tree,
            target_name=(
                class_target.qualified_name
            ),
            call_line=0,
            call_executes_during_module_initialization=False,
            ordered_candidates=(
                class_target,
            ),
            same_file_candidates=(
                class_target,
            ),
        )
    )

    if (
        stable_class_target is None
        or not _class_allows_direct_instance_method_proof(
            tree=target_tree,
            class_target=class_target,
        )
        or _named_receiver_attribute_mutation_exists(
            tree=tree,
            receiver_name=receiver_name,
            member_name=member_name,
        )
    ):
        return None

    member_candidates = (
        _ordered_unique_targets(
            qualified_symbols.get(
                (
                    class_target.source_path,
                    (
                        f"{class_target.qualified_name}"
                        f".{member_name}"
                    ),
                ),
                (),
            )
        )
    )

    if len(
        member_candidates
    ) != 1:
        return None

    member_target = (
        member_candidates[0]
    )

    if _confirmed_class_member_target(
        tree=target_tree,
        class_target=class_target,
        member_target=member_target,
    ) is None:
        return None

    return CallResolution(
        source_path=source_path,
        evidence=evidence,
        status=(
            CallResolutionStatus
            .RESOLVED_INTERNAL
        ),
        candidate_targets=(
            member_target,
        ),
        resolved_target=member_target,
        proof=(
            CallResolutionProof
            .LOCAL_INSTANCE_CONSTRUCTOR_BINDING
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

    qualified_symbols = (
        _build_qualified_symbol_index(
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
            is CallTargetKind.ATTRIBUTE
        ):
            attribute_resolution = (
                _resolve_module_attribute_call(
                    source_path=source_path,
                    evidence=evidence,
                    symbols=symbols,
                    import_resolutions=(
                        import_resolutions
                    ),
                    symbol_tables=(
                        symbol_tables
                    ),
                    syntax_trees=(
                        syntax_trees
                    ),
                )
            )

            if attribute_resolution is not None:
                resolutions.append(
                    attribute_resolution
                )

                continue

            class_attribute_resolution = (
                _resolve_class_attribute_call(
                    source_path=source_path,
                    evidence=evidence,
                    top_level_symbols=(
                        symbols
                    ),
                    qualified_symbols=(
                        qualified_symbols
                    ),
                    import_resolutions=(
                        import_resolutions
                    ),
                    symbol_tables=(
                        symbol_tables
                    ),
                    syntax_trees=(
                        syntax_trees
                    ),
                )
            )

            if (
                class_attribute_resolution
                is not None
            ):
                resolutions.append(
                    class_attribute_resolution
                )

                continue

            instance_attribute_resolution = (
                _resolve_local_instance_attribute_call(
                    source_path=source_path,
                    evidence=evidence,
                    qualified_symbols=(
                        qualified_symbols
                    ),
                    prior_resolutions=(
                        resolutions
                    ),
                    symbol_tables=(
                        symbol_tables
                    ),
                    syntax_trees=(
                        syntax_trees
                    ),
                )
            )

            if (
                instance_attribute_resolution
                is not None
            ):
                resolutions.append(
                    instance_attribute_resolution
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
