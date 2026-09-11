from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from project_sniffer.evidence import (
    SourceEvidence,
)


class ParseStatus(str, Enum):
    PARSED = "parsed"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    NON_TEXT_SOURCE = "non_text_source"
    INVALID_TEXT_EVIDENCE = "invalid_text_evidence"
    SYNTAX_ERROR = "syntax_error"


class SymbolKind(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"

class CallTargetKind(str, Enum):
    NAME = "name"
    ATTRIBUTE = "attribute"
    DYNAMIC = "dynamic"


@dataclass(frozen=True)
class ImportEvidence:
    module: str | None
    imported_name: str | None
    alias: str | None
    level: int
    scope: str | None
    line: int


@dataclass(frozen=True)
class SymbolEvidence:
    name: str
    qualified_name: str
    kind: SymbolKind
    line: int
    end_line: int | None

@dataclass(frozen=True)
class CallEvidence:
    target_kind: CallTargetKind
    target_parts: tuple[str, ...]
    scope: str | None
    line: int

@dataclass(frozen=True)
class ParsedSource:
    source: SourceEvidence
    status: ParseStatus
    parser_id: str | None
    imports: tuple[ImportEvidence, ...] = ()
    symbols: tuple[SymbolEvidence, ...] = ()
    calls: tuple[CallEvidence, ...] = ()
    error_type: str | None = None
    error_message: str | None = None
    error_line: int | None = None
