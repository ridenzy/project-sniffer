from __future__ import annotations

from project_sniffer.tracing.models import (
    DependencyGraph,
    ImportResolution,
    ImportResolutionStatus,
)


def _requested_label(
    resolution: ImportResolution,
) -> str:
    if not resolution.requested_modules:
        return "<none>"

    return ", ".join(
        resolution.requested_modules
    )


def _candidate_label(
    resolution: ImportResolution,
) -> str:
    if not resolution.candidate_paths:
        return "<none>"

    return ", ".join(
        resolution.candidate_paths
    )


def render_dependency_graph(
    graph: DependencyGraph,
) -> str:
    resolved = tuple(
        item
        for item in graph.import_resolutions
        if (
            item.status
            is ImportResolutionStatus.RESOLVED_INTERNAL
        )
    )

    unresolved = tuple(
        item
        for item in graph.import_resolutions
        if (
            item.status
            is ImportResolutionStatus.UNRESOLVED
        )
    )

    ambiguous = tuple(
        item
        for item in graph.import_resolutions
        if (
            item.status
            is ImportResolutionStatus.AMBIGUOUS
        )
    )

    invalid_relative = tuple(
        item
        for item in graph.import_resolutions
        if (
            item.status
            is ImportResolutionStatus.INVALID_RELATIVE_IMPORT
        )
    )

    lines = [
        "# Dependency Trace",
        "",
        "## Summary",
        "",
        f"- Source nodes: {len(graph.nodes)}",
        f"- Import resolutions: {len(graph.import_resolutions)}",
        f"- Confirmed internal edges: {len(graph.edges)}",
        f"- Resolved internal imports: {len(resolved)}",
        f"- Unresolved imports: {len(unresolved)}",
        f"- Ambiguous imports: {len(ambiguous)}",
        f"- Invalid relative imports: {len(invalid_relative)}",
        "",
        "## Confirmed internal dependencies",
        "",
    ]

    if graph.edges:
        for edge in graph.edges:
            scope = (
                edge.scope
                if edge.scope is not None
                else "<module>"
            )

            lines.append(
                "- "
                f"`{edge.source_path}` "
                f"→ `{edge.target_path}` "
                f"(line {edge.line}, scope `{scope}`)"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Unresolved imports",
            "",
        ]
    )

    if unresolved:
        for resolution in unresolved:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"requested "
                f"`{_requested_label(resolution)}`"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Ambiguous imports",
            "",
        ]
    )

    if ambiguous:
        for resolution in ambiguous:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"requested "
                f"`{_requested_label(resolution)}`; "
                f"candidates: "
                f"`{_candidate_label(resolution)}`"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Invalid relative imports",
            "",
        ]
    )

    if invalid_relative:
        for resolution in invalid_relative:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line}"
            )
    else:
        lines.append(
            "- None."
        )

    return (
        "\n".join(
            lines
        )
        + "\n"
    )
