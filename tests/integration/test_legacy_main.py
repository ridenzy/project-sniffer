from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main as legacy_main


class LegacyMainCompatibilityTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.original_cwd = Path.cwd()

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.workspace = Path(
            self.temporary_directory.name
        )

        self.personal_registry_path = (
            self.workspace
            / "private-config"
            / "personal_ignores.json"
        )

        self.personal_registry_patcher = patch(
            (
                "project_sniffer.config.loader."
                "get_personal_registry_path"
            ),
            return_value=self.personal_registry_path,
        )

        self.personal_registry_patcher.start()

        os.chdir(
            self.workspace
        )

        self.project = (
            self.workspace
            / "legacy-fixture"
        )

        (
            self.project
            / "src"
        ).mkdir(
            parents=True
        )

        (
            self.project
            / "docs"
            / "private"
        ).mkdir(
            parents=True
        )

        (
            self.project
            / "generated.egg-info"
        ).mkdir()

        (
            self.project
            / "src"
            / "app.py"
        ).write_text(
            'VALUE = "visible"\n',
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "docs"
            / "private"
            / "private.txt"
        ).write_text(
            "private\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "generated.egg-info"
            / "PKG-INFO"
        ).write_text(
            "generated\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "personal_ignores.json"
        ).write_text(
            "{}\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / ".gitignore"
        ).write_text(
            "docs/private/\n"
            "*.egg-info/\n"
            "personal_ignores.json\n",
            encoding="utf-8",
            newline="\n",
        )

    def tearDown(
        self,
    ) -> None:
        self.personal_registry_patcher.stop()

        os.chdir(
            self.original_cwd
        )

        self.temporary_directory.cleanup()

    def test_legacy_entry_point_uses_packaged_runtime(
        self,
    ) -> None:
        status = legacy_main.main(
            [
                str(
                    self.project
                )
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            self.workspace
            / "reports"
            / "legacy-fixture"
        )

        architecture_path = (
            report_directory
            / "legacy-fixture-architecture.md"
        )

        report_path = (
            report_directory
            / "legacy-fixture-project-report.md"
        )

        self.assertTrue(
            architecture_path.is_file()
        )

        self.assertTrue(
            report_path.is_file()
        )

        architecture = (
            architecture_path.read_text(
                encoding="utf-8"
            )
        )

        report = report_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "src/",
            architecture,
        )

        self.assertIn(
            "# `src/app.py`",
            report,
        )

        self.assertNotIn(
            "docs/private",
            architecture,
        )

        self.assertNotIn(
            "generated.egg-info",
            architecture,
        )

        self.assertNotIn(
            "# `personal_ignores.json`",
            report,
        )


if __name__ == "__main__":
    unittest.main()
