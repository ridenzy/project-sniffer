from __future__ import annotations

import unittest
from pathlib import Path

from project_sniffer.evidence import (
    SourceEvidence,
    SourceLanguage,
)
from project_sniffer.parsing import (
    ParseStatus,
    SymbolKind,
    get_parser_definition,
    parse_source_evidence,
)
from project_sniffer.reading import (
    FileReadResult,
    FileReadStatus,
)
from project_sniffer.scanning import (
    ScannedFile,
)


class ParsingTests(
    unittest.TestCase
):
    def evidence(
        self,
        relative_path: str,
        language: SourceLanguage,
        content: str | None,
        *,
        status: FileReadStatus = (
            FileReadStatus.TEXT
        ),
    ) -> SourceEvidence:
        scanned_file = ScannedFile(
            absolute_path=(
                Path("/tmp/project")
                / relative_path
            ),
            relative_path=relative_path,
        )

        result = FileReadResult(
            scanned_file=scanned_file,
            status=status,
            content=content,
            resolved_path=(
                scanned_file.absolute_path
            ),
            size_bytes=(
                len(
                    content.encode(
                        "utf-8"
                    )
                )
                if content is not None
                else None
            ),
            is_symlink=False,
        )

        return SourceEvidence(
            read_result=result,
            language=language,
        )

    def test_initial_registry_supports_python(
        self,
    ) -> None:
        definition = (
            get_parser_definition(
                SourceLanguage.PYTHON
            )
        )

        self.assertIsNotNone(
            definition
        )

        self.assertIsNone(
            get_parser_definition(
                SourceLanguage.JAVASCRIPT
            )
        )

    def test_unsupported_language_is_explicit(
        self,
    ) -> None:
        evidence = self.evidence(
            "src/app.js",
            SourceLanguage.JAVASCRIPT,
            "console.log('hello');\n",
        )

        parsed = (
            parse_source_evidence(
                evidence
            )
        )

        self.assertIs(
            parsed.source,
            evidence,
        )

        self.assertIs(
            parsed.status,
            ParseStatus.UNSUPPORTED_LANGUAGE,
        )

        self.assertIsNone(
            parsed.parser_id
        )

    def test_non_text_source_is_not_parsed(
        self,
    ) -> None:
        evidence = self.evidence(
            "src/app.py",
            SourceLanguage.PYTHON,
            None,
            status=FileReadStatus.BINARY,
        )

        parsed = (
            parse_source_evidence(
                evidence
            )
        )

        self.assertIs(
            parsed.status,
            ParseStatus.NON_TEXT_SOURCE,
        )

    def test_invalid_text_evidence_is_explicit(
        self,
    ) -> None:
        evidence = self.evidence(
            "src/app.py",
            SourceLanguage.PYTHON,
            None,
        )

        parsed = (
            parse_source_evidence(
                evidence
            )
        )

        self.assertIs(
            parsed.status,
            ParseStatus.INVALID_TEXT_EVIDENCE,
        )

    def test_python_syntax_error_is_evidence(
        self,
    ) -> None:
        evidence = self.evidence(
            "src/broken.py",
            SourceLanguage.PYTHON,
            (
                "def broken(:\n"
                "    pass\n"
            ),
        )

        parsed = (
            parse_source_evidence(
                evidence
            )
        )

        self.assertIs(
            parsed.status,
            ParseStatus.SYNTAX_ERROR,
        )

        self.assertEqual(
            parsed.error_type,
            "SyntaxError",
        )

        self.assertEqual(
            parsed.error_line,
            1,
        )

    def test_python_imports_and_symbols_are_normalized(
        self,
    ) -> None:
        source = (
            "import os\n"
            "import json as js\n"
            "from .helpers import work as do_work\n"
            "\n"
            "class Worker:\n"
            "    def run(self):\n"
            "        import pathlib\n"
            "        return do_work()\n"
            "\n"
            "async def main():\n"
            "    return Worker()\n"
        )

        evidence = self.evidence(
            "src/example.py",
            SourceLanguage.PYTHON,
            source,
        )

        parsed = (
            parse_source_evidence(
                evidence
            )
        )

        self.assertIs(
            parsed.status,
            ParseStatus.PARSED,
        )

        self.assertEqual(
            parsed.parser_id,
            "python-stdlib-ast",
        )

        imports = tuple(
            (
                item.module,
                item.imported_name,
                item.alias,
                item.level,
                item.scope,
                item.line,
            )
            for item in parsed.imports
        )

        self.assertEqual(
            imports,
            (
                (
                    "os",
                    None,
                    None,
                    0,
                    None,
                    1,
                ),
                (
                    "json",
                    None,
                    "js",
                    0,
                    None,
                    2,
                ),
                (
                    "helpers",
                    "work",
                    "do_work",
                    1,
                    None,
                    3,
                ),
                (
                    "pathlib",
                    None,
                    None,
                    0,
                    "Worker.run",
                    7,
                ),
            ),
        )

        symbols = tuple(
            (
                item.name,
                item.qualified_name,
                item.kind,
                item.line,
            )
            for item in parsed.symbols
        )

        self.assertEqual(
            symbols,
            (
                (
                    "Worker",
                    "Worker",
                    SymbolKind.CLASS,
                    5,
                ),
                (
                    "run",
                    "Worker.run",
                    SymbolKind.FUNCTION,
                    6,
                ),
                (
                    "main",
                    "main",
                    SymbolKind.ASYNC_FUNCTION,
                    10,
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
