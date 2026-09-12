from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_sniffer.architecture_builder import (
    build_architecture,
)
from project_sniffer.scanning import (
    scan_project,
)


class ProjectScannerTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.project = (
            Path(
                self.temporary_directory.name
            )
            / "fixture-project"
        )

        (
            self.project
            / "src"
        ).mkdir(
            parents=True
        )

        (
            self.project
            / "package.egg-info"
        ).mkdir()

        (
            self.project
            / "node_modules"
        ).mkdir()

        (
            self.project
            / "src"
            / "app.py"
        ).write_text(
            "VALUE = 1\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "package.egg-info"
            / "PKG-INFO"
        ).write_text(
            "generated\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "node_modules"
            / "package.js"
        ).write_text(
            "generated\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "settings.bak"
        ).write_text(
            "backup\n",
            encoding="utf-8",
            newline="\n",
        )

    def tearDown(
        self,
    ) -> None:
        self.temporary_directory.cleanup()

    def test_scan_manifest_applies_exact_and_glob_rules(
        self,
    ) -> None:
        manifest = scan_project(
            self.project,
            {
                "IGNORE_FOLDERS": [
                    "node_modules",
                    "*.egg-info",
                ],
                "IGNORE_FILES": [
                    "*.bak",
                ],
            },
        )

        relative_files = {
            scanned_file.relative_path
            for scanned_file in manifest.files
        }

        self.assertEqual(
            relative_files,
            {
                "src/app.py",
            },
        )

        self.assertNotIn(
            "package.egg-info",
            manifest.directories,
        )

        self.assertNotIn(
            "node_modules",
            manifest.directories,
        )

    def test_explicit_output_directory_is_excluded(
        self,
    ) -> None:
        output_directory = (
            self.project
            / "analysis"
            / "fixture-project"
        )

        output_directory.mkdir(
            parents=True
        )

        (
            output_directory
            / "old-report.md"
        ).write_text(
            "generated\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            self.project,
            {},
            excluded_directories=(
                output_directory,
            ),
        )

        relative_files = {
            scanned_file.relative_path
            for scanned_file in manifest.files
        }

        self.assertNotIn(
            (
                "analysis/fixture-project/"
                "old-report.md"
            ),
            relative_files,
        )

    def test_architecture_build_uses_no_second_walk(
        self,
    ) -> None:
        with patch(
            (
                "project_sniffer.scanning."
                "project_scanner.os.walk"
            ),
            wraps=os.walk,
        ) as walk:
            manifest = scan_project(
                self.project,
                {
                    "IGNORE_FOLDERS": [
                        "*.egg-info",
                        "node_modules",
                    ],
                    "IGNORE_FILES": [
                        "*.bak",
                    ],
                },
            )

            architecture = (
                build_architecture(
                    manifest
                )
            )

        self.assertEqual(
            walk.call_count,
            1,
        )

        self.assertIn(
            "src/",
            architecture,
        )

        self.assertNotIn(
            "package.egg-info",
            architecture,
        )


    def test_project_relative_config_rule_filters_only_target_path(
        self,
    ) -> None:
        first_private = (
            self.project
            / "docs"
            / "private"
        )

        second_private = (
            self.project
            / "src"
            / "docs"
            / "private"
        )

        first_private.mkdir(
            parents=True
        )

        second_private.mkdir(
            parents=True
        )

        (
            first_private
            / "hidden.txt"
        ).write_text(
            "hidden\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            second_private
            / "visible.txt"
        ).write_text(
            "visible\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            self.project,
            {
                "IGNORE_FOLDERS": [
                    "docs/private",
                    "*.egg-info",
                    "node_modules",
                ],
                "IGNORE_FILES": [
                    "*.bak",
                ],
            },
        )

        relative_files = {
            scanned_file.relative_path
            for scanned_file in manifest.files
        }

        self.assertNotIn(
            "docs/private/hidden.txt",
            relative_files,
        )

        self.assertIn(
            "src/docs/private/visible.txt",
            relative_files,
        )

    def test_root_gitignore_filters_files_and_supports_negation(
        self,
    ) -> None:
        (
            self.project
            / ".gitignore"
        ).write_text(
            "/generated/\n"
            "*.tmp\n"
            "!keep.tmp\n",
            encoding="utf-8",
            newline="\n",
        )

        generated = (
            self.project
            / "generated"
        )

        generated.mkdir()

        (
            generated
            / "ignored.txt"
        ).write_text(
            "generated\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "drop.tmp"
        ).write_text(
            "drop\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "keep.tmp"
        ).write_text(
            "keep\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            self.project,
            {
                "IGNORE_FOLDERS": [
                    "*.egg-info",
                    "node_modules",
                ],
                "IGNORE_FILES": [
                    "*.bak",
                ],
            },
        )

        relative_files = {
            scanned_file.relative_path
            for scanned_file in manifest.files
        }

        self.assertNotIn(
            "generated/ignored.txt",
            relative_files,
        )

        self.assertNotIn(
            "drop.tmp",
            relative_files,
        )

        self.assertIn(
            "keep.tmp",
            relative_files,
        )

    def test_nested_gitignore_can_override_parent_file_rule(
        self,
    ) -> None:
        (
            self.project
            / ".gitignore"
        ).write_text(
            "*.log\n",
            encoding="utf-8",
            newline="\n",
        )

        source = (
            self.project
            / "src"
        )

        (
            source
            / ".gitignore"
        ).write_text(
            "!keep.log\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            source
            / "keep.log"
        ).write_text(
            "keep\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            source
            / "drop.log"
        ).write_text(
            "drop\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            self.project,
            {
                "IGNORE_FOLDERS": [
                    "*.egg-info",
                    "node_modules",
                ],
                "IGNORE_FILES": [
                    "*.bak",
                ],
            },
        )

        relative_files = {
            scanned_file.relative_path
            for scanned_file in manifest.files
        }

        self.assertIn(
            "src/keep.log",
            relative_files,
        )

        self.assertNotIn(
            "src/drop.log",
            relative_files,
        )

    def test_excluded_parent_directory_is_not_reincluded_by_nested_gitignore(
        self,
    ) -> None:
        (
            self.project
            / ".gitignore"
        ).write_text(
            "/generated/\n",
            encoding="utf-8",
            newline="\n",
        )

        generated = (
            self.project
            / "generated"
        )

        generated.mkdir()

        (
            generated
            / ".gitignore"
        ).write_text(
            "!keep.txt\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            generated
            / "keep.txt"
        ).write_text(
            "keep\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            self.project,
            {
                "IGNORE_FOLDERS": [
                    "*.egg-info",
                    "node_modules",
                ],
                "IGNORE_FILES": [
                    "*.bak",
                ],
            },
        )

        relative_files = {
            scanned_file.relative_path
            for scanned_file in manifest.files
        }

        self.assertNotIn(
            "generated/keep.txt",
            relative_files,
        )

    def test_gitignore_can_be_disabled_for_scoped_scan(
        self,
    ) -> None:
        docs_root = (
            self.project
            / "docs"
            / "private"
        )

        docs_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            docs_root
            / ".gitignore"
        ).write_text(
            "hidden.md\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            docs_root
            / "hidden.md"
        ).write_text(
            "private documentation\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            docs_root,
            {
                "IGNORE_FOLDERS": [],
                "IGNORE_FILES": [],
            },
            apply_gitignore=False,
        )

        self.assertIn(
            "hidden.md",
            {
                item.relative_path
                for item in manifest.files
            },
        )


    def test_scoped_scan_uses_project_relative_ignore_prefix(
        self,
    ) -> None:
        docs_root = (
            self.project
            / "docs"
            / "private"
        )

        archive = (
            docs_root
            / "archive"
        )

        archive.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            docs_root
            / "keep.md"
        ).write_text(
            "keep\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            archive
            / "old.md"
        ).write_text(
            "old\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = scan_project(
            docs_root,
            {
                "IGNORE_FOLDERS": [
                    "docs/private/archive",
                ],
                "IGNORE_FILES": [],
            },
            apply_gitignore=False,
            ignore_path_prefix="docs/private",
        )

        paths = {
            item.relative_path
            for item in manifest.files
        }

        self.assertIn(
            "keep.md",
            paths,
        )

        self.assertNotIn(
            "archive/old.md",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
