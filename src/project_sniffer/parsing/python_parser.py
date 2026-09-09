from __future__ import annotations

import ast

from project_sniffer.evidence import (
    SourceEvidence,
    SourceLanguage,
)
from project_sniffer.parsing.models import (
    ImportEvidence,
    ParsedSource,
    ParseStatus,
    SymbolEvidence,
    SymbolKind,
)


PYTHON_AST_PARSER_ID = "python-stdlib-ast"


class _PythonEvidenceVisitor(
    ast.NodeVisitor
):
    def __init__(
        self,
    ) -> None:
        self.imports: list[
            ImportEvidence
        ] = []

        self.symbols: list[
            SymbolEvidence
        ] = []

        self._scope: list[str] = []

    @property
    def scope_name(
        self,
    ) -> str | None:
        if not self._scope:
            return None

        return ".".join(
            self._scope
        )

    def qualified_name(
        self,
        name: str,
    ) -> str:
        if not self._scope:
            return name

        return ".".join(
            (
                *self._scope,
                name,
            )
        )

    def record_symbol(
        self,
        node: ast.AST,
        name: str,
        kind: SymbolKind,
    ) -> None:
        self.symbols.append(
            SymbolEvidence(
                name=name,
                qualified_name=(
                    self.qualified_name(
                        name
                    )
                ),
                kind=kind,
                line=getattr(
                    node,
                    "lineno",
                    0,
                ),
                end_line=getattr(
                    node,
                    "end_lineno",
                    None,
                ),
            )
        )

    def visit_Import(
        self,
        node: ast.Import,
    ) -> None:
        for alias in node.names:
            self.imports.append(
                ImportEvidence(
                    module=alias.name,
                    imported_name=None,
                    alias=alias.asname,
                    level=0,
                    scope=self.scope_name,
                    line=node.lineno,
                )
            )

    def visit_ImportFrom(
        self,
        node: ast.ImportFrom,
    ) -> None:
        for alias in node.names:
            self.imports.append(
                ImportEvidence(
                    module=node.module,
                    imported_name=alias.name,
                    alias=alias.asname,
                    level=node.level,
                    scope=self.scope_name,
                    line=node.lineno,
                )
            )

    def visit_ClassDef(
        self,
        node: ast.ClassDef,
    ) -> None:
        self.record_symbol(
            node,
            node.name,
            SymbolKind.CLASS,
        )

        self._scope.append(
            node.name
        )

        self.generic_visit(
            node
        )

        self._scope.pop()

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        self.record_symbol(
            node,
            node.name,
            SymbolKind.FUNCTION,
        )

        self._scope.append(
            node.name
        )

        self.generic_visit(
            node
        )

        self._scope.pop()

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self.record_symbol(
            node,
            node.name,
            SymbolKind.ASYNC_FUNCTION,
        )

        self._scope.append(
            node.name
        )

        self.generic_visit(
            node
        )

        self._scope.pop()


def parse_python_source(
    evidence: SourceEvidence,
) -> ParsedSource:
    if (
        evidence.language
        is not SourceLanguage.PYTHON
    ):
        raise ValueError(
            "parse_python_source requires "
            "Python SourceEvidence."
        )

    content = (
        evidence
        .read_result
        .content
    )

    if content is None:
        raise ValueError(
            "parse_python_source requires "
            "readable source content."
        )

    relative_path = (
        evidence
        .read_result
        .scanned_file
        .relative_path
    )

    try:
        tree = ast.parse(
            content,
            filename=relative_path,
            type_comments=True,
        )

    except SyntaxError as error:
        return ParsedSource(
            source=evidence,
            status=(
                ParseStatus.SYNTAX_ERROR
            ),
            parser_id=(
                PYTHON_AST_PARSER_ID
            ),
            error_type="SyntaxError",
            error_message=error.msg,
            error_line=error.lineno,
        )

    visitor = (
        _PythonEvidenceVisitor()
    )

    visitor.visit(
        tree
    )

    return ParsedSource(
        source=evidence,
        status=ParseStatus.PARSED,
        parser_id=PYTHON_AST_PARSER_ID,
        imports=tuple(
            visitor.imports
        ),
        symbols=tuple(
            visitor.symbols
        ),
    )
