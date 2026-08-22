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


if __name__ == "__main__":
    unittest.main()
