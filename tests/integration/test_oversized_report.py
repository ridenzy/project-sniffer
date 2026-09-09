from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from project_sniffer.cli import main
from project_sniffer.reading import (
    DEFAULT_MAX_SOURCE_BYTES,
)


class OversizedReportIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
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
        self.personal_registry_patcher.stop()

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
