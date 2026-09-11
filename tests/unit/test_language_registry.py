from __future__ import annotations

import unittest
from pathlib import Path

from project_sniffer.evidence import (
    LANGUAGE_DEFINITIONS,
    SourceLanguage,
    classify_source_language,
)


class LanguageRegistryTests(
    unittest.TestCase
):
    def test_every_source_language_has_one_definition(
        self,
    ) -> None:
        registered = {
            definition.language
            for definition in LANGUAGE_DEFINITIONS
        }

        self.assertEqual(
            registered,
            set(
                SourceLanguage
            ),
        )

        self.assertEqual(
            len(
                LANGUAGE_DEFINITIONS
            ),
            len(
                SourceLanguage
            ),
        )

    def test_required_general_languages_are_registered(
        self,
    ) -> None:
        required = {
            SourceLanguage.C,
            SourceLanguage.CPP,
            SourceLanguage.CSHARP,
            SourceLanguage.GO,
            SourceLanguage.RUST,
            SourceLanguage.JAVA,
            SourceLanguage.KOTLIN,
            SourceLanguage.PYTHON,
            SourceLanguage.JAVASCRIPT,
            SourceLanguage.TYPESCRIPT,
            SourceLanguage.PHP,
            SourceLanguage.RUBY,
            SourceLanguage.SWIFT,
        }

        registered = {
            definition.language
            for definition in LANGUAGE_DEFINITIONS
        }

        self.assertTrue(
            required.issubset(
                registered
            )
        )

    def test_general_programming_suffixes(
        self,
    ) -> None:
        cases = {
            "src/main.c": SourceLanguage.C,
            "src/main.cpp": SourceLanguage.CPP,
            "src/Program.cs": SourceLanguage.CSHARP,
            "scripts/example.csx": SourceLanguage.CSHARP,
            "cmd/server.go": SourceLanguage.GO,
            "src/lib.rs": SourceLanguage.RUST,
            "src/main.zig": SourceLanguage.ZIG,
            "src/Main.java": SourceLanguage.JAVA,
            "src/Main.kt": SourceLanguage.KOTLIN,
            "src/main.swift": SourceLanguage.SWIFT,
            "src/main.dart": SourceLanguage.DART,
        }

        for path, expected in cases.items():
            with self.subTest(
                path=path
            ):
                self.assertEqual(
                    classify_source_language(
                        path
                    ),
                    expected,
                )

    def test_domain_specific_suffixes(
        self,
    ) -> None:
        cases = {
            "database/function.pgsql": SourceLanguage.PLPGSQL,
            "database/query.sql": SourceLanguage.SQL,
            "database/package.plsql": SourceLanguage.PLSQL,
            "schema/api.graphql": SourceLanguage.GRAPHQL,
            "schema/message.proto": SourceLanguage.PROTOBUF,
            "infra/main.tf": SourceLanguage.HCL,
            "infra/system.nix": SourceLanguage.NIX,
            "contracts/module.move": SourceLanguage.MOVE,
            "contracts/example.vy": SourceLanguage.VYPER,
            "shader/main.wgsl": SourceLanguage.WGSL,
            "hardware/core.sv": SourceLanguage.SYSTEMVERILOG,
            "hardware/core.vhdl": SourceLanguage.VHDL,
        }

        for path, expected in cases.items():
            with self.subTest(
                path=path
            ):
                self.assertEqual(
                    classify_source_language(
                        path
                    ),
                    expected,
                )

    def test_compound_suffix_has_priority(
        self,
    ) -> None:
        self.assertEqual(
            classify_source_language(
                "views/account.blade.php"
            ),
            SourceLanguage.BLADE,
        )

        self.assertEqual(
            classify_source_language(
                "types/generated.d.ts"
            ),
            SourceLanguage.TYPESCRIPT,
        )

    def test_case_sensitive_c_and_cpp_suffixes(
        self,
    ) -> None:
        self.assertEqual(
            classify_source_language(
                "src/example.c"
            ),
            SourceLanguage.C,
        )

        self.assertEqual(
            classify_source_language(
                "src/example.C"
            ),
            SourceLanguage.CPP,
        )

    def test_special_basenames(
        self,
    ) -> None:
        cases = {
            "Dockerfile": SourceLanguage.DOCKERFILE,
            "Containerfile": SourceLanguage.DOCKERFILE,
            "Makefile": SourceLanguage.MAKEFILE,
            "CMakeLists.txt": SourceLanguage.CMAKE,
            "BUILD.bazel": SourceLanguage.STARLARK,
            "Gemfile": SourceLanguage.RUBY,
            ".editorconfig": SourceLanguage.INI,
        }

        for path, expected in cases.items():
            with self.subTest(
                path=path
            ):
                self.assertEqual(
                    classify_source_language(
                        path
                    ),
                    expected,
                )

    def test_ambiguous_extensions_are_not_guessed(
        self,
    ) -> None:
        for path in (
            "src/header.h",
            "src/example.m",
            "src/example.pl",
            "src/example.sol",
            "src/example.v",
        ):
            with self.subTest(
                path=path
            ):
                self.assertEqual(
                    classify_source_language(
                        path
                    ),
                    SourceLanguage.UNKNOWN,
                )

    def test_public_language_document_covers_registry(
        self,
    ) -> None:
        documentation = Path(
            "docs/public/language-support.md"
        ).read_text(
            encoding="utf-8"
        )

        for definition in (
            LANGUAGE_DEFINITIONS
        ):
            marker = (
                f"| `{definition.language.value}` |"
            )

            with self.subTest(
                language=(
                    definition.language.value
                )
            ):
                self.assertIn(
                    marker,
                    documentation,
                )

        self.assertIn(
            (
                "| `python` | Python | programming | "
                "Yes | `python` |  |"
            ),
            documentation,
        )

        self.assertIn(
            (
                "| `python` | `python-stdlib-ast` | Parsed | "
                "imports; classes; functions; async functions; "
                "call sites |"
            ),
            documentation,
        )


if __name__ == "__main__":
    unittest.main()
