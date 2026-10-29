from __future__ import annotations

from project_sniffer.tracing.models import (
    CallEndpoint,
    CallIndex,
    CallIndexEntry,
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
)


def _endpoint_sort_key(
    endpoint: CallEndpoint,
) -> tuple[str, str]:
    return (
        endpoint.path,
        endpoint.symbol or "",
    )


def _edge_sort_key(
    edge: DependencyEdge,
) -> tuple[
    str,
    str,
    int,
    str,
    str,
]:
    return (
        edge.source_path,
        edge.scope or "",
        edge.line,
        edge.target_path,
        edge.target_symbol or "",
    )


def _freeze_entries(
    groups: dict[
        CallEndpoint,
        list[DependencyEdge],
    ],
) -> tuple[
    CallIndexEntry,
    ...,
]:
    return tuple(
        CallIndexEntry(
            endpoint=endpoint,
            edges=tuple(
                sorted(
                    groups[endpoint],
                    key=_edge_sort_key,
                )
            ),
        )
        for endpoint
        in sorted(
            groups,
            key=_endpoint_sort_key,
        )
    )


def build_call_index(
    graph: DependencyGraph,
) -> CallIndex:
    outbound: dict[
        CallEndpoint,
        list[DependencyEdge],
    ] = {}

    inbound: dict[
        CallEndpoint,
        list[DependencyEdge],
    ] = {}

    for edge in graph.edges:
        if (
            edge.kind
            is not DependencyKind.CALL
        ):
            continue

        if edge.target_symbol is None:
            continue

        caller = CallEndpoint(
            path=edge.source_path,
            symbol=edge.scope,
        )

        callee = CallEndpoint(
            path=edge.target_path,
            symbol=edge.target_symbol,
        )

        outbound.setdefault(
            caller,
            [],
        ).append(
            edge
        )

        inbound.setdefault(
            callee,
            [],
        ).append(
            edge
        )

    return CallIndex(
        outbound=_freeze_entries(
            outbound
        ),
        inbound=_freeze_entries(
            inbound
        ),
    )
