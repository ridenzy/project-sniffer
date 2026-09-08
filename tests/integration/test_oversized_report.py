from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from project_sniffer.cli import main
from project_sniffer.reading import (
    DEFAULT_MAX_SOURCE_BYTES,
)


class OversizedReportIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
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

    def tearDown(self) -> None:
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

    def test_cli_report_skips_oversized_source(
        self,
    ) -> None:
        oversized_path = (
            self.project
            / "src"
            / "oversized.txt"
        )

        marker = (
            b"OVERSIZED-CONTENT-MUST-STAY-OUT\n"
        )

        prefix = (
            marker
            + (
                b"A"
                * (
                    2048
                    - len(marker)
                )
            )
        )

        with oversized_path.open(
            "wb"
        ) as file_handle:
            file_handle.write(
                prefix
            )

            file_handle.seek(
                DEFAULT_MAX_SOURCE_BYTES
            )

            file_handle.write(
                b"Z"
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

        report = report_path.read_text(
            encoding="utf-8"
        )

        output = stdout.getvalue()

        self.assertIn(
            "# `src/visible.txt`",
            report,
        )

        self.assertNotIn(
            "# `src/oversized.txt`",
            report,
        )

        self.assertNotIn(
            marker.decode(
                "utf-8"
            ).strip(),
            report,
        )

        self.assertIn(
            "[SKIP oversized] "
            "src/oversized.txt -> "
            f"{DEFAULT_MAX_SOURCE_BYTES + 1} bytes",
            output,
        )

        self.assertIn(
            "Skipped oversized files: 1",
            output,
        )


if __name__ == "__main__":
    unittest.main()
