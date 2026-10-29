from __future__ import annotations

import unittest
from pathlib import Path

from project_sniffer.evidence import (
    SourceLanguage,
    build_source_evidence,
    classify_source_language,
)
from project_sniffer.reading import (
    FileReadResult,
    FileReadStatus,
)
from project_sniffer.scanning import (
    ScannedFile,
)


class SourceEvidenceTests(
    unittest.TestCase
):
    def read_result(
        self,
        relative_path: str,
        *,
        status: FileReadStatus = FileReadStatus.TEXT,
    ) -> FileReadResult:
        content = (
            "content\n"
            if status is FileReadStatus.TEXT
            else None
        )

        scanned_file = ScannedFile(
            absolute_path=(
                Path("/tmp/project")
                / relative_path
            ),
            relative_path=relative_path,
        )

        return FileReadResult(
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

    def test_common_source_extensions_are_classified(
        self,
    ) -> None:
        cases = {
            "src/app.py": SourceLanguage.PYTHON,
            "src/types.pyi": SourceLanguage.PYTHON,
            "web/app.js": SourceLanguage.JAVASCRIPT,
            "web/component.jsx": SourceLanguage.JAVASCRIPT,
            "web/app.ts": SourceLanguage.TYPESCRIPT,
            "web/component.tsx": SourceLanguage.TYPESCRIPT,
            "public/index.php": SourceLanguage.PHP,
            "config/app.json": SourceLanguage.JSON,
            "config/app.yaml": SourceLanguage.YAML,
            "pyproject.toml": SourceLanguage.TOML,
            "database/schema.sql": SourceLanguage.SQL,
            "scripts/setup.sh": SourceLanguage.SHELL,
            "templates/index.html": SourceLanguage.HTML,
            "styles/site.css": SourceLanguage.CSS,
            "README.md": SourceLanguage.MARKDOWN,
            "notes.txt": SourceLanguage.PLAIN_TEXT,
        }

        for relative_path, expected in cases.items():
            with self.subTest(
                relative_path=relative_path
            ):
                self.assertEqual(
                    classify_source_language(
                        relative_path
                    ),
                    expected,
                )

    def test_known_suffix_matching_is_case_insensitive(
        self,
    ) -> None:
        self.assertEqual(
            classify_source_language(
                "src/EXAMPLE.PY"
            ),
            SourceLanguage.PYTHON,
        )

    def test_special_filenames_are_classified(
        self,
    ) -> None:
        cases = {
            ".editorconfig": SourceLanguage.INI,
            ".gitignore": SourceLanguage.PLAIN_TEXT,
            "DCO": SourceLanguage.PLAIN_TEXT,
            "Dockerfile": SourceLanguage.DOCKERFILE,
            "LICENSE": SourceLanguage.PLAIN_TEXT,
            "Makefile": SourceLanguage.MAKEFILE,
        }

        for relative_path, expected in cases.items():
            with self.subTest(
                relative_path=relative_path
            ):
                self.assertEqual(
                    classify_source_language(
                        relative_path
                    ),
                    expected,
                )

    def test_unknown_language_uses_text_markdown_fence(
        self,
    ) -> None:
        language = classify_source_language(
            "assets/example.unknown-extension"
        )

        self.assertEqual(
            language,
            SourceLanguage.UNKNOWN,
        )

        self.assertEqual(
            language.markdown_fence_label,
            "text",
        )

    def test_shell_language_uses_bash_markdown_fence(
        self,
    ) -> None:
        language = classify_source_language(
            "scripts/install.sh"
        )

        self.assertEqual(
            language,
            SourceLanguage.SHELL,
        )

        self.assertEqual(
            language.markdown_fence_label,
            "bash",
        )

    def test_source_evidence_preserves_order_and_read_identity(
        self,
    ) -> None:
        first = self.read_result(
            "src/first.py"
        )

        second = self.read_result(
            "web/second.ts"
        )

        evidence = build_source_evidence(
            (
                second,
                first,
            )
        )

        self.assertEqual(
            tuple(
                item.language
                for item in evidence
            ),
            (
                SourceLanguage.TYPESCRIPT,
                SourceLanguage.PYTHON,
            ),
        )

        self.assertIs(
            evidence[0].read_result,
            second,
        )

        self.assertIs(
            evidence[1].read_result,
            first,
        )

    def test_language_metadata_does_not_change_read_status(
        self,
    ) -> None:
        binary = self.read_result(
            "web/app.js",
            status=FileReadStatus.BINARY,
        )

        evidence = build_source_evidence(
            (binary,)
        )

        self.assertEqual(
            evidence[0].language,
            SourceLanguage.JAVASCRIPT,
        )

        self.assertIs(
            evidence[0].read_result.status,
            FileReadStatus.BINARY,
        )


if __name__ == "__main__":
    unittest.main()
