from __future__ import annotations

from project_sniffer.indexing import (
    SemanticProjectIndex,
)
from project_sniffer.tracing.models import (
    CallResolutionStatus,
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    ImportResolutionStatus,
)
from project_sniffer.tracing.python_calls import (
    resolve_python_calls,
)
from project_sniffer.tracing.python_imports import (
    resolve_python_imports,
)


def build_dependency_graph(
    index: SemanticProjectIndex,
) -> DependencyGraph:
    nodes = tuple(
        dict.fromkeys(
            (
                parsed
                .source
                .read_result
                .scanned_file
                .relative_path
            )
            for parsed
            in index.parsed_sources
        )
    )

    import_resolutions = (
        resolve_python_imports(
            index
        )
    )

    call_resolutions = (
        resolve_python_calls(
            index,
            import_resolutions,
        )
    )

    edges: list[
        DependencyEdge
    ] = []

    for resolution in import_resolutions:
        if (
            resolution.status
            is not (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            )
        ):
            continue

        target_path = (
            resolution.target_path
        )

        if target_path is None:
            continue

        edges.append(
            DependencyEdge(
                source_path=(
                    resolution.source_path
                ),
                target_path=target_path,
                kind=DependencyKind.IMPORT,
                line=(
                    resolution
                    .evidence
                    .line
                ),
                scope=(
                    resolution
                    .evidence
                    .scope
                ),
                resolution=resolution,
            )
        )

    for resolution in call_resolutions:
        if (
            resolution.status
            is not (
                CallResolutionStatus
                .RESOLVED_INTERNAL
            )
        ):
            continue

        target = (
            resolution.resolved_target
        )

        if target is None:
            continue

        edges.append(
            DependencyEdge(
                source_path=(
                    resolution.source_path
                ),
                target_path=(
                    target.source_path
                ),
                kind=DependencyKind.CALL,
                line=(
                    resolution
                    .evidence
                    .line
                ),
                scope=(
                    resolution
                    .evidence
                    .scope
                ),
                resolution=resolution,
                target_symbol=(
                    target.qualified_name
                ),
            )
        )

    return DependencyGraph(
        nodes=nodes,
        import_resolutions=(
            import_resolutions
        ),
        call_resolutions=(
            call_resolutions
        ),
        edges=tuple(
            edges
        ),
    )