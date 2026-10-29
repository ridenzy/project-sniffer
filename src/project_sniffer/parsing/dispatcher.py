from __future__ import annotations

from project_sniffer.evidence import (
    SourceEvidence,
)
from project_sniffer.parsing.models import (
    ParsedSource,
    ParseStatus,
)
from project_sniffer.parsing.registry import (
    get_parser_definition,
)
from project_sniffer.reading import (
    FileReadStatus,
)


def parse_source_evidence(
    evidence: SourceEvidence,
) -> ParsedSource:
    result = evidence.read_result

    if (
        result.status
        is not FileReadStatus.TEXT
    ):
        return ParsedSource(
            source=evidence,
            status=(
                ParseStatus.NON_TEXT_SOURCE
            ),
            parser_id=None,
        )

    if result.content is None:
        return ParsedSource(
            source=evidence,
            status=(
                ParseStatus.INVALID_TEXT_EVIDENCE
            ),
            parser_id=None,
            error_type="InvalidTextEvidence",
            error_message=(
                "TEXT FileReadResult has "
                "no source content."
            ),
        )

    definition = (
        get_parser_definition(
            evidence.language
        )
    )

    if definition is None:
        return ParsedSource(
            source=evidence,
            status=(
                ParseStatus.UNSUPPORTED_LANGUAGE
            ),
            parser_id=None,
        )

    return definition.parser(
        evidence
    )
