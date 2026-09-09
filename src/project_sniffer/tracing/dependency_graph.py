from __future__ import annotations

from project_sniffer.indexing import (
    SemanticProjectIndex,
)
from project_sniffer.tracing.models import (
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    ImportResolutionStatus,
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

    edges: list[
        DependencyEdge
    ] = []

    for resolution in import_resolutions:
        if (
            resolution.status
            is not ImportResolutionStatus.RESOLVED_INTERNAL
        ):
            continue

        target_path = resolution.target_path

        if target_path is None:
            continue

        edges.append(
            DependencyEdge(
                source_path=resolution.source_path,
                target_path=target_path,
                kind=DependencyKind.IMPORT,
                line=resolution.evidence.line,
                scope=resolution.evidence.scope,
                resolution=resolution,
            )
        )

    return DependencyGraph(
        nodes=nodes,
        import_resolutions=import_resolutions,
        edges=tuple(
            edges
        ),
    )
