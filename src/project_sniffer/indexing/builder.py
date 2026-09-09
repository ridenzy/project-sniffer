from __future__ import annotations

from collections.abc import Sequence

from project_sniffer.evidence import (
    SourceEvidence,
)
from project_sniffer.indexing.models import (
    IndexedImport,
    IndexedSymbol,
    SemanticProjectIndex,
)
from project_sniffer.parsing import (
    ParseStatus,
    parse_source_evidence,
)


def build_semantic_project_index(
    source_evidence: Sequence[SourceEvidence],
) -> SemanticProjectIndex:
    parsed_sources = tuple(
        parse_source_evidence(
            evidence
        )
        for evidence in source_evidence
    )

    imports: list[
        IndexedImport
    ] = []

    symbols: list[
        IndexedSymbol
    ] = []

    for parsed in parsed_sources:
        if (
            parsed.status
            is not ParseStatus.PARSED
        ):
            continue

        source_path = (
            parsed
            .source
            .read_result
            .scanned_file
            .relative_path
        )

        imports.extend(
            IndexedImport(
                source_path=source_path,
                evidence=item,
            )
            for item in parsed.imports
        )

        symbols.extend(
            IndexedSymbol(
                source_path=source_path,
                evidence=item,
            )
            for item in parsed.symbols
        )

    return SemanticProjectIndex(
        parsed_sources=parsed_sources,
        imports=tuple(
            imports
        ),
        symbols=tuple(
            symbols
        ),
    )
