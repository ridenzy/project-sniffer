from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import (
    redirect_stderr,
    redirect_stdout,
)
from pathlib import Path

from project_sniffer.cli import main


class ProjectSnifferAnalysisCliTests(
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

        self.original_xdg_config_home = (
            os.environ.get(
                "XDG_CONFIG_HOME"
            )
        )

        self.config_home = (
            self.workspace
            / "config-home"
        )

        self.personal_registry_path = (
            self.config_home
            / "project-sniffer"
            / "personal_ignores.json"
        )

        os.environ[
            "XDG_CONFIG_HOME"
        ] = str(
            self.config_home
        )

        os.chdir(
            self.workspace
        )

        self.project = (
            self.workspace
            / "fixture-project"
        )

        source = (
            self.project
            / "src"
        )

        source.mkdir(
            parents=True
        )

        (
            source
            / "example.py"
        ).write_text(
            "def greet(name):\n"
            "    return f\"Hello, {name}\"\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / "project.json"
        ).write_text(
            "{\n"
            '    "name": "fixture-project"\n'
            "}\n",
            encoding="utf-8",
            newline="\n",
        )

    def tearDown(
        self,
    ) -> None:
        if (
            self.original_xdg_config_home
            is None
        ):
            os.environ.pop(
                "XDG_CONFIG_HOME",
                None,
            )

        else:
            os.environ[
                "XDG_CONFIG_HOME"
            ] = self.original_xdg_config_home

        os.chdir(
            self.original_cwd
        )

        self.temporary_directory.cleanup()

    def test_relative_project_path_generates_both_reports(
        self,
    ) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            status = main(
                [
                    "--project",
                    "fixture-project",
                    "--architecture",
                    "--report",
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            self.workspace
            / "reports"
            / "fixture-project"
        )

        architecture_path = (
            report_directory
            / (
                "fixture-project"
                "-architecture.md"
            )
        )

        report_path = (
            report_directory
            / (
                "fixture-project"
                "-project-report.md"
            )
        )

        self.assertTrue(
            architecture_path.is_file()
        )

        self.assertTrue(
            report_path.is_file()
        )

        self.assertIn(
            "example.py",
            architecture_path.read_text(
                encoding="utf-8"
            ),
        )

        self.assertIn(
            "# `src/example.py`",
            report_path.read_text(
                encoding="utf-8"
            ),
        )

    def test_architecture_only_does_not_create_source_report(
        self,
    ) -> None:
        output_base_directory = (
            self.workspace
            / "analysis"
        )

        status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
                "--output",
                str(
                    output_base_directory
                ),
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            output_base_directory
            / "fixture-project"
        )

        self.assertTrue(
            (
                report_directory
                / (
                    "fixture-project"
                    "-architecture.md"
                )
            ).is_file()
        )

        self.assertFalse(
            (
                report_directory
                / (
                    "fixture-project"
                    "-project-report.md"
                )
            ).exists()
        )

    def test_project_without_analyzer_is_rejected(
        self,
    ) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(
            stdout
        ), redirect_stderr(
            stderr
        ):
            with self.assertRaises(
                SystemExit
            ) as raised:
                main(
                    [
                        "--project",
                        str(
                            self.project
                        ),
                    ]
                )

        self.assertEqual(
            raised.exception.code,
            1,
        )

        self.assertIn(
            "select at least one",
            stderr.getvalue(),
        )

    def test_missing_project_returns_invalid_input_code(
        self,
    ) -> None:
        stderr = io.StringIO()

        with redirect_stderr(
            stderr
        ):
            status = main(
                [
                    "--project",
                    "missing-project",
                    "--architecture",
                ]
            )

        self.assertEqual(
            status,
            1,
        )

        self.assertIn(
            "does not exist",
            stderr.getvalue(),
        )

    def test_personal_ignore_file_is_not_auto_created(
        self,
    ) -> None:
        personal_path = (
            self.workspace
            / "personal_ignores.json"
        )

        self.assertFalse(
            personal_path.exists()
        )

        status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        self.assertFalse(
            personal_path.exists()
        )

    def test_existing_legacy_personal_ignore_is_used(
        self,
    ) -> None:
        self.personal_registry_path.parent.mkdir(
            parents=True
        )

        self.personal_registry_path.write_text(
            "{\n"
            '    "IGNORE_FOLDERS": ["src"],\n'
            '    "IGNORE_FILES": []\n'
            "}\n",
            encoding="utf-8",
            newline="\n",
        )

        output_base_directory = (
            self.workspace
            / "personal-output"
        )

        status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
                "--output",
                str(
                    output_base_directory
                ),
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        architecture_text = (
            output_base_directory
            / "fixture-project"
            / (
                "fixture-project"
                "-architecture.md"
            )
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "src/",
            architecture_text,
        )

    def test_working_directory_personal_ignore_is_not_used(
        self,
    ) -> None:
        cwd_personal_path = (
            self.workspace
            / "personal_ignores.json"
        )

        cwd_personal_path.write_text(
            "{\n"
            '    "IGNORE_FOLDERS": ["src"],\n'
            '    "IGNORE_FILES": []\n'
            "}\n",
            encoding="utf-8",
            newline="\n",
        )

        output_base_directory = (
            self.workspace
            / "cwd-isolation-output"
        )

        status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
                "--output",
                str(
                    output_base_directory
                ),
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        architecture_text = (
            output_base_directory
            / "fixture-project"
            / (
                "fixture-project"
                "-architecture.md"
            )
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "src/",
            architecture_text,
        )


if __name__ == "__main__":
    unittest.main()
