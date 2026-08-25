from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if SOURCE_ROOT.is_dir():
    source_root_value = str(
        SOURCE_ROOT
    )

    if source_root_value not in sys.path:
        sys.path.insert(
            0,
            source_root_value,
        )

from project_sniffer.application import (
    run_analysis,
)


def main(
    argv: list[str] | None = None,
) -> int:
    """
    Compatibility entry point for the original positional command.

    The authoritative runtime lives in the project_sniffer package. This
    wrapper preserves:

        python3 main.py /path/to/project

    while delegating scanning, configuration, ignore handling, architecture,
    report generation, and grouped output to the packaged implementation.
    """

    arguments = list(
        sys.argv[1:]
        if argv is None
        else argv
    )

    if len(arguments) != 1:
        print(
            "Usage: python3 main.py <project_path>"
        )
        return 1

    return run_analysis(
        project_value=arguments[0],
        architecture_requested=True,
        report_requested=True,
        output_value=None,
        working_directory=Path.cwd(),
    )


if __name__ == "__main__":
    main()
