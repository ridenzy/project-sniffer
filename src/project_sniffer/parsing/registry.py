from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from project_sniffer.evidence import (
    SourceEvidence,
    SourceLanguage,
)
from project_sniffer.parsing.models import (
    ParsedSource,
)
from project_sniffer.parsing.python_parser import (
    PYTHON_AST_PARSER_ID,
    parse_python_source,
)


ParserFunction = Callable[
    [SourceEvidence],
    ParsedSource,
]


@dataclass(frozen=True)
class ParserDefinition:
    language: SourceLanguage
    parser_id: str
    parser: ParserFunction


PARSER_DEFINITIONS = (
    ParserDefinition(
        language=SourceLanguage.PYTHON,
        parser_id=PYTHON_AST_PARSER_ID,
        parser=parse_python_source,
    ),
)


_DEFINITION_BY_LANGUAGE = {
    definition.language: definition
    for definition in PARSER_DEFINITIONS
}


def get_parser_definition(
    language: SourceLanguage,
) -> ParserDefinition | None:
    return _DEFINITION_BY_LANGUAGE.get(
        language
    )
