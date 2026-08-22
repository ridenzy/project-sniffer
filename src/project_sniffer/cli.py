from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from project_sniffer import __version__
from project_sniffer.application import (
    run_analysis,
)


_DESCRIPTION = """\
Project Sniffer
Local-first, read-only repository intelligence.

Generate deterministic repository evidence without executing
target-project code.
"""

_EPILOG = """\
Implemented analyzers in this Phase 1 checkpoint:
  --architecture    Generate the current project-tree architecture report.
  --report          Generate the current readable Markdown source report.

Examples:
  sniff --project ./frontend --architecture
  sniff --project ./frontend --report
  sniff --project ./frontend --architecture --report
  sniff --project ./frontend --architecture --output ./analysis

Still planned for later phases:
  --trace
  --secret
  --database
  --all
  --config
  --strict
  --verbose
  --quiet

Safety model:
  Project Sniffer inspects target projects read-only. The core does not
  execute target-project code, install target dependencies, connect to
  target databases, or make ordinary static-analysis network requests.
"""


class ProjectSnifferArgumentParser(
    argparse.ArgumentParser
):
    """Argument parser using Project Sniffer's invalid-input code."""

    def error(
        self,
        message: str,
    ) -> None:
        self.print_usage(
            sys.stderr
        )

        self.exit(
            1,
            (
                f"{self.prog}: error: "
                f"{message}\n"
            ),
        )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the Project Sniffer command-line parser."""

    parser = ProjectSnifferArgumentParser(
        prog="sniff",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        formatter_class=(
            argparse.RawDescriptionHelpFormatter
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help=(
            "Show the installed Project Sniffer "
            "version and exit."
        ),
    )

    parser.add_argument(
        "--project",
        metavar="PATH",
        help=(
            "Full or relative path to the "
            "project to inspect."
        ),
    )

    analyzers = (
        parser.add_argument_group(
            "implemented analyzers"
        )
    )

    analyzers.add_argument(
        "--architecture",
        action="store_true",
        help=(
            "Generate the current architecture "
            "tree report."
        ),
    )

    analyzers.add_argument(
        "--report",
        action="store_true",
        help=(
            "Generate the current readable "
            "Markdown source report."
        ),
    )

    parser.add_argument(
        "--output",
        metavar="PATH",
        help=(
            "Override the base output directory. "
            "A project-named subdirectory is "
            "created inside it."
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the installed Project Sniffer CLI."""

    parser = build_parser()

    args = parser.parse_args(
        argv
    )

    requested_analyzer = (
        args.architecture
        or args.report
    )

    if (
        not requested_analyzer
        and args.project is None
        and args.output is None
    ):
        parser.print_help()
        return 0

    if args.project is None:
        parser.error(
            "--project is required when "
            "running an analyzer"
        )

    if not requested_analyzer:
        parser.error(
            "select at least one implemented "
            "analyzer: --architecture or --report"
        )

    return run_analysis(
        project_value=args.project,
        architecture_requested=(
            args.architecture
        ),
        report_requested=args.report,
        output_value=args.output,
        working_directory=Path.cwd(),
    )
