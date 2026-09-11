from __future__ import annotations

from dataclasses import dataclass

from project_sniffer.parsing import (
    CallEvidence,
    ImportEvidence,
    ParsedSource,
    SymbolEvidence,
)

@dataclass(frozen=True)
class IndexedCall:
    source_path: str
    evidence: CallEvidence

@dataclass(frozen=True)
class IndexedImport:
    source_path: str
    evidence: ImportEvidence


@dataclass(frozen=True)
class IndexedSymbol:
    source_path: str
    evidence: SymbolEvidence

@dataclass(frozen=True)
class SemanticProjectIndex:
    parsed_sources: tuple[ParsedSource, ...]
    imports: tuple[IndexedImport, ...]
    symbols: tuple[IndexedSymbol, ...]
    calls: tuple[IndexedCall, ...]
