from __future__ import annotations

from collections.abc import Sequence

from project_sniffer.evidence.language_registry import (
    classify_path_language,
)
from project_sniffer.evidence.models import (
    SourceEvidence,
    SourceLanguage,
)
from project_sniffer.reading import (
    FileReadResult,
)


def classify_source_language(
    relative_path: str,
) -> SourceLanguage:
    """
    Classify a manifest-relative path without reading source content.

    The canonical path-recognition rules live in language_registry.
    Unknown or ambiguous paths remain explicitly UNKNOWN.
    """

    return classify_path_language(
        relative_path
    )


def build_source_evidence(
    read_results: Sequence[FileReadResult],
) -> tuple[SourceEvidence, ...]:
    """
    Attach deterministic language metadata to existing safe-read evidence.

    Input ordering and FileReadResult object identity are preserved.
    No target-project file is reopened.
    """

    return tuple(
        SourceEvidence(
            read_result=result,
            language=classify_source_language(
                result.scanned_file.relative_path
            ),
        )
        for result in read_results
    )