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
from unittest.mock import patch

from project_sniffer.cli import main
import project_sniffer.application as application


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
        self.personal_registry_patcher.stop()

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

        self.assertIn(
            "**Project:** `fixture-project`",
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
        self.assertFalse(
            self.personal_registry_path.exists()
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
            self.personal_registry_path.exists()
        )

    def test_existing_project_profile_personal_ignore_is_used(
        self,
    ) -> None:
        self.personal_registry_path.parent.mkdir(
            parents=True
        )

        self.personal_registry_path.write_text(
            "{\n"
            '    "schema_version": 1,\n'
            '    "projects": {\n'
            '        "fixture-project": {\n'
            '            "IGNORE_FOLDERS": ["src"],\n'
            '            "IGNORE_FILES": []\n'
            "        }\n"
            "    }\n"
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

    def test_docs_only_generates_public_and_private_reports(
        self,
    ) -> None:
        public_docs = (
            self.project
            / "docs"
            / "public"
        )

        private_docs = (
            self.project
            / "docs"
            / "private"
        )

        public_docs.mkdir(
            parents=True
        )

        private_docs.mkdir(
            parents=True
        )

        (
            public_docs
            / "guide.md"
        ).write_text(
            "public guide\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            public_docs
            / "git-ignored.md"
        ).write_text(
            "docs report still sees me\n",
            encoding="utf-8",
            newline="\n",
        )

        assets = (
            public_docs
            / "assets"
        )

        assets.mkdir()

        (
            assets
            / "diagram.bin"
        ).write_bytes(
            b"binary\x00documentation"
        )

        internal = (
            public_docs
            / "internal"
        )

        internal.mkdir()

        (
            internal
            / "hidden.md"
        ).write_text(
            "personal ignore hides me\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            private_docs
            / "notes.md"
        ).write_text(
            "private notes\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            self.project
            / ".gitignore"
        ).write_text(
            "docs/private/\n"
            "docs/public/git-ignored.md\n",
            encoding="utf-8",
            newline="\n",
        )

        self.personal_registry_path.parent.mkdir(
            parents=True
        )

        self.personal_registry_path.write_text(
            "{\n"
            '    "schema_version": 1,\n'
            '    "projects": {\n'
            '        "fixture-project": {\n'
            '            "IGNORE_FOLDERS": [\n'
            '                "docs/public/internal"\n'
            "            ],\n"
            '            "IGNORE_FILES": []\n'
            "        }\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
            newline="\n",
        )

        output_base = (
            self.workspace
            / "docs-output"
        )

        stdout = io.StringIO()

        with redirect_stdout(
            stdout
        ):
            status = main(
                [
                    "--project",
                    str(
                        self.project
                    ),
                    "--docs",
                    "--output",
                    str(
                        output_base
                    ),
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            output_base
            / "fixture-project"
        )

        public_report = (
            report_directory
            / "fixture-project-public-docs-report.md"
        )

        private_report = (
            report_directory
            / "fixture-project-private-docs-report.md"
        )

        self.assertTrue(
            public_report.is_file()
        )

        self.assertTrue(
            private_report.is_file()
        )

        public_text = public_report.read_text(
            encoding="utf-8"
        )

        private_text = private_report.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "# `guide.md`",
            public_text,
        )

        self.assertIn(
            "# `git-ignored.md`",
            public_text,
        )

        self.assertNotIn(
            "internal/hidden.md",
            public_text,
        )

        self.assertNotIn(
            "diagram.bin",
            public_text,
        )

        self.assertIn(
            "# `notes.md`",
            private_text,
        )

        self.assertFalse(
            (
                report_directory
                / "docs"
            ).exists()
        )

        self.assertFalse(
            (
                report_directory
                / "fixture-project-architecture.md"
            ).exists()
        )

        self.assertFalse(
            (
                report_directory
                / "fixture-project-project-report.md"
            ).exists()
        )

        rendered = stdout.getvalue()

        self.assertIn(
            "docs/public/: found",
            rendered,
        )

        self.assertIn(
            "docs/private/: found",
            rendered,
        )

        self.assertIn(
            "Skipped binary files: 1",
            rendered,
        )

        self.assertIn(
            "Documentation reports generated: 2",
            rendered,
        )

    def test_docs_private_personal_ignore_can_be_approved(
        self,
    ) -> None:
        private_docs = (
            self.project
            / "docs"
            / "private"
        )

        private_docs.mkdir(
            parents=True
        )

        (
            private_docs
            / "notes.md"
        ).write_text(
            "private notes\n",
            encoding="utf-8",
            newline="\n",
        )

        self.personal_registry_path.parent.mkdir(
            parents=True
        )

        self.personal_registry_path.write_text(
            "{\n"
            '    "schema_version": 1,\n'
            '    "projects": {\n'
            '        "fixture-project": {\n'
            '            "IGNORE_FOLDERS": [\n'
            '                "private"\n'
            "            ],\n"
            '            "IGNORE_FILES": []\n'
            "        }\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
            newline="\n",
        )

        output_base = (
            self.workspace
            / "private-approved-output"
        )

        stdout = io.StringIO()

        with patch(
            "builtins.input",
            return_value="y",
        ) as prompt, redirect_stdout(
            stdout
        ):
            status = main(
                [
                    "--project",
                    str(
                        self.project
                    ),
                    "--docs",
                    "--output",
                    str(
                        output_base
                    ),
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        prompt.assert_called_once_with(
            "Generate the docs/private/ "
            "report? [y/N]: "
        )

        private_report = (
            output_base
            / "fixture-project"
            / "fixture-project-private-docs-report.md"
        )

        self.assertTrue(
            private_report.is_file()
        )

        self.assertIn(
            "# `notes.md`",
            private_report.read_text(
                encoding="utf-8"
            ),
        )

        rendered = stdout.getvalue()

        self.assertIn(
            "WARNING: docs/private/",
            rendered,
        )

        self.assertIn(
            "override approved",
            rendered,
        )

        self.assertIn(
            "private-scope exclusion overridden",
            rendered,
        )

        self.assertIn(
            "Documentation reports generated: 1",
            rendered,
        )

    def test_docs_private_personal_ignore_can_be_declined(
        self,
    ) -> None:
        private_docs = (
            self.project
            / "docs"
            / "private"
        )

        private_docs.mkdir(
            parents=True
        )

        (
            private_docs
            / "notes.md"
        ).write_text(
            "private notes\n",
            encoding="utf-8",
            newline="\n",
        )

        self.personal_registry_path.parent.mkdir(
            parents=True
        )

        self.personal_registry_path.write_text(
            "{\n"
            '    "schema_version": 1,\n'
            '    "projects": {\n'
            '        "fixture-project": {\n'
            '            "IGNORE_FOLDERS": [\n'
            '                "private"\n'
            "            ],\n"
            '            "IGNORE_FILES": []\n'
            "        }\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
            newline="\n",
        )

        output_base = (
            self.workspace
            / "private-declined-output"
        )

        output_directory = (
            output_base
            / "fixture-project"
        )

        output_directory.mkdir(
            parents=True
        )

        private_report = (
            output_directory
            / "fixture-project-private-docs-report.md"
        )

        private_report.write_text(
            "stale private report\n",
            encoding="utf-8",
            newline="\n",
        )

        self.assertTrue(
            private_report.is_file()
        )

        stdout = io.StringIO()

        with patch(
            "builtins.input",
            return_value="n",
        ) as prompt, redirect_stdout(
            stdout
        ):
            status = main(
                [
                    "--project",
                    str(
                        self.project
                    ),
                    "--docs",
                    "--output",
                    str(
                        output_base
                    ),
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        prompt.assert_called_once_with(
            "Generate the docs/private/ "
            "report? [y/N]: "
        )

        self.assertFalse(
            private_report.exists()
        )

        rendered = stdout.getvalue()

        self.assertIn(
            "WARNING: docs/private/",
            rendered,
        )

        self.assertIn(
            "override declined",
            rendered,
        )

        self.assertIn(
            "docs/private/: found",
            rendered,
        )

        self.assertIn(
            "Report: not generated",
            rendered,
        )

        self.assertIn(
            "Documentation reports generated: 0",
            rendered,
        )

    def test_docs_only_reports_missing_documentation_directories(
        self,
    ) -> None:
        output_base = (
            self.workspace
            / "docs-missing-output"
        )

        stdout = io.StringIO()

        with redirect_stdout(
            stdout
        ):
            status = main(
                [
                    "--project",
                    str(
                        self.project
                    ),
                    "--docs",
                    "--output",
                    str(
                        output_base
                    ),
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            output_base
            / "fixture-project"
        )

        self.assertTrue(
            report_directory.is_dir()
        )

        self.assertFalse(
            (
                report_directory
                / "fixture-project-public-docs-report.md"
            ).exists()
        )

        self.assertFalse(
            (
                report_directory
                / "fixture-project-private-docs-report.md"
            ).exists()
        )

        rendered = stdout.getvalue()

        self.assertIn(
            "docs/public/: not found",
            rendered,
        )

        self.assertIn(
            "docs/private/: not found",
            rendered,
        )

        self.assertIn(
            "Documentation reports generated: 0",
            rendered,
        )

    def test_in_project_custom_output_is_excluded_on_repeat_scan(
        self,
    ) -> None:
        output_base = (
            self.project
            / "analysis"
        )

        first_status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
                "--report",
                "--output",
                str(
                    output_base
                ),
            ]
        )

        self.assertEqual(
            first_status,
            0,
        )

        second_status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
                "--report",
                "--output",
                str(
                    output_base
                ),
            ]
        )

        self.assertEqual(
            second_status,
            0,
        )

        report_directory = (
            output_base
            / "fixture-project"
        )

        architecture_text = (
            report_directory
            / (
                "fixture-project"
                "-architecture.md"
            )
        ).read_text(
            encoding="utf-8"
        )

        report_text = (
            report_directory
            / (
                "fixture-project"
                "-project-report.md"
            )
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            (
                "analysis/fixture-project/"
                "fixture-project-architecture.md"
            ),
            architecture_text,
        )

        self.assertNotIn(
            (
                "# `analysis/fixture-project/"
                "fixture-project-architecture.md`"
            ),
            report_text,
        )


    def test_target_gitignore_filters_architecture_and_report(
        self,
    ) -> None:
        (
            self.project
            / ".gitignore"
        ).write_text(
            "/generated/\n"
            "*.tmp\n",
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
            / "scratch.tmp"
        ).write_text(
            "temporary\n",
            encoding="utf-8",
            newline="\n",
        )

        output_base = (
            self.workspace
            / "gitignore-output"
        )

        status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--architecture",
                "--report",
                "--output",
                str(
                    output_base
                ),
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            output_base
            / "fixture-project"
        )

        architecture_text = (
            report_directory
            / (
                "fixture-project"
                "-architecture.md"
            )
        ).read_text(
            encoding="utf-8"
        )

        report_text = (
            report_directory
            / (
                "fixture-project"
                "-project-report.md"
            )
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "generated/",
            architecture_text,
        )

        self.assertNotIn(
            "scratch.tmp",
            architecture_text,
        )

        self.assertNotIn(
            "# `generated/ignored.txt`",
            report_text,
        )

        self.assertNotIn(
            "# `scratch.tmp`",
            report_text,
        )

        self.assertIn(
            "# `src/example.py`",
            report_text,
        )

    def test_trace_only_generates_dependency_trace(
        self,
    ) -> None:
        source = (
            self.project
            / "src"
        )

        (
            source
            / "helper.py"
        ).write_text(
            (
                "def work():\n"
                "    return True\n"
            ),
            encoding="utf-8",
            newline="\n",
        )

        (
            source
            / "app.py"
        ).write_text(
            (
                "from helper import work\n"
                "\n"
                "def run():\n"
                "    return work()\n"
            ),
            encoding="utf-8",
            newline="\n",
        )

        output_base = (
            self.workspace
            / "trace-output"
        )

        status = main(
            [
                "--project",
                str(
                    self.project
                ),
                "--trace",
                "--output",
                str(
                    output_base
                ),
            ]
        )

        self.assertEqual(
            status,
            0,
        )

        report_directory = (
            output_base
            / "fixture-project"
        )

        trace_path = (
            report_directory
            / "fixture-project-trace.md"
        )

        self.assertTrue(
            trace_path.is_file()
        )

        trace_text = trace_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "# Dependency Trace",
            trace_text,
        )

        self.assertIn(
            (
                "`src/app.py` "
                "→ `src/helper.py`"
            ),
            trace_text,
        )

        self.assertFalse(
            (
                report_directory
                / "fixture-project-project-report.md"
            ).exists()
        )

        self.assertFalse(
            (
                report_directory
                / "fixture-project-architecture.md"
            ).exists()
        )

    def test_report_and_trace_share_one_source_read(
        self,
    ) -> None:
        output_base = (
            self.workspace
            / "shared-evidence-output"
        )

        with patch.object(
            application,
            "read_manifest_files",
            wraps=application.read_manifest_files,
        ) as reader:
            status = main(
                [
                    "--project",
                    str(
                        self.project
                    ),
                    "--report",
                    "--trace",
                    "--output",
                    str(
                        output_base
                    ),
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        self.assertEqual(
            reader.call_count,
            1,
        )

        report_directory = (
            output_base
            / "fixture-project"
        )

        self.assertTrue(
            (
                report_directory
                / "fixture-project-project-report.md"
            ).is_file()
        )

        self.assertTrue(
            (
                report_directory
                / "fixture-project-trace.md"
            ).is_file()
        )
if __name__ == "__main__":
    unittest.main()
