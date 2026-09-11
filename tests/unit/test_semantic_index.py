from __future__ import annotations

from typing import get_type_hints

import unittest
from pathlib import Path

from project_sniffer.evidence import (
    SourceEvidence,
    SourceLanguage,
)
from project_sniffer.indexing import (
    IndexedCall,
    build_semantic_project_index,
)
from project_sniffer.parsing import (
    CallEvidence,
    CallTargetKind,
    ParseStatus,
    SymbolKind,
)
from project_sniffer.reading import (
    FileReadResult,
    FileReadStatus,
)
from project_sniffer.scanning import (
    ScannedFile,
)


class SemanticProjectIndexTests(
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

    def test_index_flattens_parsed_imports_and_symbols(
        self,
    ) -> None:
        app = self.evidence(
            "pkg/app.py",
            SourceLanguage.PYTHON,
            (
                "from .worker import Worker\n"
                "\n"
                "def main():\n"
                "    return Worker()\n"
            ),
        )

        worker = self.evidence(
            "pkg/worker.py",
            SourceLanguage.PYTHON,
            (
                "class Worker:\n"
                "    def run(self):\n"
                "        return True\n"
            ),
        )

        javascript = self.evidence(
            "web/app.js",
            SourceLanguage.JAVASCRIPT,
            "console.log('hello');\n",
        )

        index = build_semantic_project_index(
            (
                app,
                worker,
                javascript,
            )
        )

        self.assertEqual(
            tuple(
                parsed.status
                for parsed
                in index.parsed_sources
            ),
            (
                ParseStatus.PARSED,
                ParseStatus.PARSED,
                ParseStatus.UNSUPPORTED_LANGUAGE,
            ),
        )

        self.assertIs(
            index.parsed_sources[0].source,
            app,
        )

        self.assertEqual(
            tuple(
                (
                    item.source_path,
                    item.evidence.module,
                    item.evidence.imported_name,
                    item.evidence.level,
                )
                for item in index.imports
            ),
            (
                (
                    "pkg/app.py",
                    "worker",
                    "Worker",
                    1,
                ),
            ),
        )

        self.assertEqual(
            tuple(
                (
                    item.source_path,
                    item.evidence.qualified_name,
                    item.evidence.kind,
                )
                for item in index.symbols
            ),
            (
                (
                    "pkg/app.py",
                    "main",
                    SymbolKind.FUNCTION,
                ),
                (
                    "pkg/worker.py",
                    "Worker",
                    SymbolKind.CLASS,
                ),
                (
                    "pkg/worker.py",
                    "Worker.run",
                    SymbolKind.FUNCTION,
                ),
            ),
        )

        self.assertEqual(
            tuple(
                (
                    item.source_path,
                    item.evidence.target_kind,
                    item.evidence.target_parts,
                    item.evidence.scope,
                    item.evidence.line,
                )
                for item in index.calls
            ),
            (
                (
                    "pkg/app.py",
                    CallTargetKind.NAME,
                    (
                        "Worker",
                    ),
                    "main",
                    4,
                ),
            ),
        )

    def test_failed_or_nontext_results_remain_visible(
        self,
    ) -> None:
        broken = self.evidence(
            "pkg/broken.py",
            SourceLanguage.PYTHON,
            "def broken(:\n",
        )

        binary = self.evidence(
            "pkg/data.py",
            SourceLanguage.PYTHON,
            None,
            status=FileReadStatus.BINARY,
        )

        index = build_semantic_project_index(
            (
                broken,
                binary,
            )
        )

        self.assertEqual(
            tuple(
                parsed.status
                for parsed
                in index.parsed_sources
            ),
            (
                ParseStatus.SYNTAX_ERROR,
                ParseStatus.NON_TEXT_SOURCE,
            ),
        )

        self.assertEqual(
            index.imports,
            (),
        )

        self.assertEqual(
            index.symbols,
            (),
        )

        self.assertEqual(
            index.calls,
            (),
        )

    def test_indexed_call_type_annotation_resolves(
        self,
    ) -> None:
        annotations = get_type_hints(
            IndexedCall
        )

        self.assertIs(
            annotations["evidence"],
            CallEvidence,
        )

if __name__ == "__main__":
    unittest.main()
