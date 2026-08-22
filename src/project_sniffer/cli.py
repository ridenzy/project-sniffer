from __future__ import annotations

import argparse
from collections.abc import Sequence

from project_sniffer import __version__


_DESCRIPTION = """\
Project Sniffer
Local-first, read-only repository intelligence.

This Phase 1 CLI foundation exposes command documentation and package version
metadata while the proven architecture/report runtime is migrated behind the
installed `sniff` command.
"""

_EPILOG = """\
Examples available in this checkpoint:
  sniff --help
  sniff -h
  sniff --version

Phase 1 commands being wired next:
  sniff --project ./frontend --architecture
  sniff --project ./frontend --report
  sniff --project ./frontend --architecture --report
  sniff --project ./frontend --architecture --output ./analysis

The analyzer examples above are intentionally documented as the next migration
slice; they are not enabled by this checkpoint yet.

Safety model:
  Project Sniffer is designed to inspect target projects read-only. The core
  does not execute target-project code, install target dependencies, connect to
  target databases, or make ordinary static-analysis network requests.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build and return the Project Sniffer command-line parser."""

    parser = argparse.ArgumentParser(
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

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the current Project Sniffer CLI foundation."""

    parser = build_parser()

    parser.parse_args(
        argv
    )

    parser.print_help()

    return 0
