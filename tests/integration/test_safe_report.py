from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from project_sniffer.cli import main


class SafeReportIntegrationTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.original_cwd = Path.cwd()

        self.original_xdg_config_home = (
            os.environ.get(
                "XDG_CONFIG_HOME"
            )
        )

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.workspace = Path(
            self.temporary_directory.name
        )

        self.config_home = (
            self.workspace
            / "config-home"
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

        (
            self.project
            / "src"
        ).mkdir(
            parents=True
        )

        (
            self.project
            / "src"
            / "visible.txt"
        ).write_text(
            "visible source\n",
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

    def create_symlink_or_skip(
        self,
        *,
        target: Path,
        link: Path,
    ) -> None:
        try:
            link.symlink_to(
                target
            )
        except (
            OSError,
            NotImplementedError,
        ) as error:
            self.skipTest(
                "symlink creation is unavailable: "
                f"{type(error).__name__}"
            )

    def test_report_does_not_follow_internal_or_escaped_file_symlinks(
        self,
    ) -> None:
        internal_target = (
            self.project
            / ".env"
        )

        internal_target.write_text(
            "INTERNAL-SYMLINK-CONTENT\n",
            encoding="utf-8",
            newline="\n",
        )

        outside_target = (
            self.workspace
            / "outside-target.txt"
        )

        outside_target.write_text(
            "OUTSIDE-SYMLINK-CONTENT\n",
            encoding="utf-8",
            newline="\n",
        )

        internal_link = (
            self.project
            / "src"
            / "internal-link.txt"
        )

        escaped_link = (
            self.project
            / "src"
            / "escaped-link.txt"
        )

        self.create_symlink_or_skip(
            target=internal_target,
            link=internal_link,
        )

        self.create_symlink_or_skip(
            target=outside_target,
            link=escaped_link,
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
                    "--report",
                ]
            )

        self.assertEqual(
            status,
            0,
        )

        report_path = (
            self.workspace
            / "reports"
            / "fixture-project"
            / "fixture-project-project-report.md"
        )

        self.assertTrue(
            report_path.is_file()
        )

        report = report_path.read_text(
            encoding="utf-8"
        )

        output = stdout.getvalue()

        self.assertIn(
            "# `src/visible.txt`",
            report,
        )

        self.assertNotIn(
            "# `.env`",
            report,
        )

        self.assertNotIn(
            "INTERNAL-SYMLINK-CONTENT",
            report,
        )

        self.assertNotIn(
            "# `src/internal-link.txt`",
            report,
        )

        self.assertNotIn(
            "# `src/escaped-link.txt`",
            report,
        )

        self.assertNotIn(
            "OUTSIDE-SYMLINK-CONTENT",
            report,
        )

        self.assertIn(
            "[SKIP symlink] "
            "src/internal-link.txt",
            output,
        )

        self.assertIn(
            "[SKIP escaped-symlink] "
            "src/escaped-link.txt",
            output,
        )


if __name__ == "__main__":
    unittest.main()
