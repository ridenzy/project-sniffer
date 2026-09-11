from __future__ import annotations

from project_sniffer.tracing.models import (
    CallResolution,
    CallResolutionStatus,
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


def _call_label(
    resolution: CallResolution,
) -> str:
    if not resolution.evidence.target_parts:
        return "<dynamic>"

    return ".".join(
        resolution.evidence.target_parts
    )


def _call_candidate_label(
    resolution: CallResolution,
) -> str:
    if not resolution.candidate_targets:
        return "<none>"

    return ", ".join(
        (
            f"{target.source_path}"
            f"::{target.qualified_name}"
        )
        for target
        in resolution.candidate_targets
    )


def _scope_label(
    scope: str | None,
) -> str:
    if scope is None:
        return "<module>"

    return scope


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

    potential_calls = tuple(
        item
        for item in graph.call_resolutions
        if (
            item.status
            is (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            )
        )
    )

    shadowed_calls = tuple(
        item
        for item in graph.call_resolutions
        if (
            item.status
            is CallResolutionStatus.SHADOWED
        )
    )

    unresolved_calls = tuple(
        item
        for item in graph.call_resolutions
        if (
            item.status
            is CallResolutionStatus.UNRESOLVED
        )
    )

    ambiguous_calls = tuple(
        item
        for item in graph.call_resolutions
        if (
            item.status
            is CallResolutionStatus.AMBIGUOUS
        )
    )

    dynamic_calls = tuple(
        item
        for item in graph.call_resolutions
        if (
            item.status
            is CallResolutionStatus.DYNAMIC
        )
    )

    lines = [
        "# Dependency Trace",
        "",
        "## Summary",
        "",
        f"- Source nodes: {len(graph.nodes)}",
        f"- Import resolutions: {len(graph.import_resolutions)}",
        f"- Call resolutions: {len(graph.call_resolutions)}",
        f"- Confirmed internal edges: {len(graph.edges)}",
        f"- Resolved internal imports: {len(resolved)}",
        f"- Unresolved imports: {len(unresolved)}",
        f"- Ambiguous imports: {len(ambiguous)}",
        f"- Invalid relative imports: {len(invalid_relative)}",
        (
            "- Potential internal calls: "
            f"{len(potential_calls)}"
        ),
        (
            "- Unresolved calls: "
            f"{len(unresolved_calls)}"
        ),
        (
            "- Ambiguous calls: "
            f"{len(ambiguous_calls)}"
        ),
        (
            "- Dynamic calls: "
            f"{len(dynamic_calls)}"
        ),
        (
            "- Shadowed calls: "
            f"{len(shadowed_calls)}"
        ),
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


    lines.extend(
        [
            "",
            (
                "## Potential internal calls "
                "(not confirmed edges)"
            ),
            "",
        ]
    )

    if potential_calls:
        for resolution in potential_calls:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"`{_call_label(resolution)}` "
                "→ candidate "
                f"`{_call_candidate_label(resolution)}` "
                f"(scope "
                f"`{_scope_label(resolution.evidence.scope)}`)"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Shadowed call candidates",
            "",
        ]
    )

    if shadowed_calls:
        for resolution in shadowed_calls:
            reason = (
                resolution.shadowed_by.value
                if resolution.shadowed_by
                is not None
                else "unknown"
            )

            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"`{_call_label(resolution)}` "
                f"shadowed by `{reason}` "
                f"(scope "
                f"`{_scope_label(resolution.evidence.scope)}`)"
            )

    else:
        lines.append(
            "- None."
        )


    lines.extend(
        [
            "",
            "## Unresolved calls",
            "",
        ]
    )

    if unresolved_calls:
        for resolution in unresolved_calls:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"`{_call_label(resolution)}` "
                f"(scope "
                f"`{_scope_label(resolution.evidence.scope)}`)"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Ambiguous call candidates",
            "",
        ]
    )

    if ambiguous_calls:
        for resolution in ambiguous_calls:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"`{_call_label(resolution)}`; "
                "candidates: "
                f"`{_call_candidate_label(resolution)}`"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Dynamic calls",
            "",
        ]
    )

    if dynamic_calls:
        for resolution in dynamic_calls:
            lines.append(
                "- "
                f"`{resolution.source_path}`:"
                f"{resolution.evidence.line} "
                f"(scope "
                f"`{_scope_label(resolution.evidence.scope)}`)"
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
