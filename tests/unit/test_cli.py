from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from project_sniffer import __version__
from project_sniffer.cli import (
    build_parser,
    main,
)


class ProjectSnifferCliTests(
    unittest.TestCase
):
    def test_help_documents_current_analyzers_and_safety_boundary(
        self,
    ) -> None:
        help_text = (
            build_parser().format_help()
        )

        required_fragments = (
            "--project",
            "--architecture",
            "--report",
            "--trace",
            "--docs",
            "docs/private",
            "--output",
            "implemented analyzers",
            "output capabilities",
            (
                "sniff --project ./frontend "
                "--architecture"
            ),
            "read-only",
        )

        for fragment in required_fragments:
            with self.subTest(
                fragment=fragment
            ):
                self.assertIn(
                    fragment,
                    help_text,
                )

        self.assertNotIn(
            "Implemented analyzers currently available:",
            help_text,
        )

        self.assertNotIn(
            "Phase 1 checkpoint",
            help_text,
        )

    def test_help_flag_exits_successfully(
        self,
    ) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            with self.assertRaises(
                SystemExit
            ) as raised:
                main(
                    ["--help"]
                )

        self.assertEqual(
            raised.exception.code,
            0,
        )

        self.assertIn(
            "usage: sniff",
            output.getvalue(),
        )

    def test_version_flag_exits_successfully(
        self,
    ) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            with self.assertRaises(
                SystemExit
            ) as raised:
                main(
                    ["--version"]
                )

        self.assertEqual(
            raised.exception.code,
            0,
        )

        self.assertEqual(
            output.getvalue().strip(),
            f"sniff {__version__}",
        )


if __name__ == "__main__":
    unittest.main()
