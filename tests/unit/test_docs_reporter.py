from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from project_sniffer.docs_reporter import (
    DocsReportError,
    build_documentation_reports,
    print_documentation_summary,
)


class DocsReporterTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.workspace = Path(
            self.temporary_directory.name
        )

        self.project = (
            self.workspace
            / "fixture-project"
        )

        self.project.mkdir()

        self.output = (
            self.workspace
            / "reports"
            / "fixture-project"
        )

    def tearDown(
        self,
    ) -> None:
        self.temporary_directory.cleanup()

    def test_public_and_gitignored_private_reports_are_generated(
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
            "docs/private/\n",
            encoding="utf-8",
            newline="\n",
        )

        summary = (
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [],
                    "IGNORE_FILES": [],
                },
            )
        )

        self.assertEqual(
            summary.generated_reports,
            2,
        )

        public_report = (
            self.output
            / "fixture-project-public-docs-report.md"
        )

        private_report = (
            self.output
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
            "# Public Documentation Report",
            public_text,
        )

        self.assertIn(
            "**Documentation root:** `docs/public/`",
            public_text,
        )

        self.assertIn(
            "# `guide.md`",
            public_text,
        )

        self.assertIn(
            "# Private Documentation Report",
            private_text,
        )

        self.assertIn(
            "**Documentation root:** `docs/private/`",
            private_text,
        )

        self.assertIn(
            "# `notes.md`",
            private_text,
        )

    def test_project_relative_ignore_applies_inside_private_scope(
        self,
    ) -> None:
        private_docs = (
            self.project
            / "docs"
            / "private"
        )

        archive = (
            private_docs
            / "archive"
        )

        archive.mkdir(
            parents=True
        )

        (
            private_docs
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

        summary = (
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [
                        "docs/private/archive",
                    ],
                    "IGNORE_FILES": [],
                },
            )
        )

        self.assertFalse(
            summary.private.ignored_by_config
        )

        report = (
            self.output
            / "fixture-project-private-docs-report.md"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "# `keep.md`",
            report,
        )

        self.assertNotIn(
            "archive/old.md",
            report,
        )

    def test_private_scope_ignore_without_approval_generates_no_report(
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
            "private\n",
            encoding="utf-8",
            newline="\n",
        )

        self.output.mkdir(
            parents=True
        )

        stale_report = (
            self.output
            / "fixture-project-private-docs-report.md"
        )

        stale_report.write_text(
            "stale private report\n",
            encoding="utf-8",
            newline="\n",
        )

        self.assertTrue(
            stale_report.is_file()
        )

        summary = (
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [
                        "docs/private",
                    ],
                    "IGNORE_FILES": [],
                },
            )
        )

        self.assertTrue(
            summary.private.exists
        )

        self.assertTrue(
            summary.private.ignored_by_config
        )

        self.assertFalse(
            summary.private.ignore_overridden
        )

        self.assertIsNone(
            summary.private.report_summary
        )

        self.assertFalse(
            stale_report.exists()
        )

    def test_private_scope_override_preserves_other_ignore_rules(
        self,
    ) -> None:
        private_docs = (
            self.project
            / "docs"
            / "private"
        )

        archive = (
            private_docs
            / "archive"
        )

        archive.mkdir(
            parents=True
        )

        (
            private_docs
            / "keep.md"
        ).write_text(
            "keep\n",
            encoding="utf-8",
            newline="\n",
        )

        (
            private_docs
            / "skip.bak"
        ).write_text(
            "skip\n",
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

        summary = (
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [
                        "private",
                        "docs/private/archive",
                    ],
                    "IGNORE_FILES": [
                        "*.bak",
                    ],
                },
                confirm_private_ignore_override=(
                    lambda: True
                ),
            )
        )

        self.assertTrue(
            summary.private.ignored_by_config
        )

        self.assertTrue(
            summary.private.ignore_overridden
        )

        report = (
            self.output
            / "fixture-project-private-docs-report.md"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "# `keep.md`",
            report,
        )

        self.assertNotIn(
            "archive/old.md",
            report,
        )

        self.assertNotIn(
            "skip.bak",
            report,
        )

    def test_missing_scopes_are_reported_without_outputs(
        self,
    ) -> None:
        summary = (
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [],
                    "IGNORE_FILES": [],
                },
            )
        )

        self.assertEqual(
            summary.generated_reports,
            0,
        )

        self.assertFalse(
            summary.public.exists
        )

        self.assertFalse(
            summary.private.exists
        )

        output = io.StringIO()

        with redirect_stdout(
            output
        ):
            print_documentation_summary(
                summary
            )

        rendered = output.getvalue()

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

    def test_symlink_scope_path_is_rejected(
        self,
    ) -> None:
        external = (
            self.workspace
            / "external-docs"
        )

        (
            external
            / "public"
        ).mkdir(
            parents=True
        )

        docs_link = (
            self.project
            / "docs"
        )

        try:
            docs_link.symlink_to(
                external,
                target_is_directory=True,
            )
        except (
            OSError,
            NotImplementedError,
        ) as error:
            self.skipTest(
                "symlink creation is unavailable: "
                f"{type(error).__name__}"
            )

        with self.assertRaises(
            DocsReportError
        ):
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [],
                    "IGNORE_FILES": [],
                },
            )

    def test_output_report_symlink_is_rejected(
        self,
    ) -> None:
        public_docs = (
            self.project
            / "docs"
            / "public"
        )

        public_docs.mkdir(
            parents=True
        )

        (
            public_docs
            / "guide.md"
        ).write_text(
            "guide\n",
            encoding="utf-8",
            newline="\n",
        )

        self.output.mkdir(
            parents=True
        )

        outside = (
            self.workspace
            / "outside.md"
        )

        outside.write_text(
            "outside\n",
            encoding="utf-8",
            newline="\n",
        )

        report_link = (
            self.output
            / "fixture-project-public-docs-report.md"
        )

        try:
            report_link.symlink_to(
                outside
            )
        except (
            OSError,
            NotImplementedError,
        ) as error:
            self.skipTest(
                "symlink creation is unavailable: "
                f"{type(error).__name__}"
            )

        with self.assertRaises(
            DocsReportError
        ):
            build_documentation_reports(
                project_path=self.project,
                output_directory=self.output,
                ignore={
                    "IGNORE_FOLDERS": [],
                    "IGNORE_FILES": [],
                },
            )

        self.assertEqual(
            outside.read_text(
                encoding="utf-8"
            ),
            "outside\n",
        )


if __name__ == "__main__":
    unittest.main();
