from __future__ import annotations

import sys
from pathlib import Path

from project_sniffer.architecture_builder import (
    build_architecture,
)
from project_sniffer.config import (
    ConfigurationError,
    load_ignore_config,
)
from project_sniffer.report_builder import (
    build_report,
)
from project_sniffer.scanner import (
    scan_project,
)


INVALID_INPUT = 1
OUTPUT_ERROR = 4


def resolve_project_path(
    project_value: str,
) -> Path:
    """
    Resolve an absolute or relative project path correctly.

    Unlike the legacy entry point, relative paths are resolved from
    the current working directory rather than being prefixed with `/`.
    """

    return (
        Path(
            project_value
        )
        .expanduser()
        .resolve()
    )


def resolve_output_directory(
    output_value: str | None,
    project_name: str,
    working_directory: Path,
) -> Path:
    """
    Resolve the project-specific report directory.

    The default base directory is:
        <working-directory>/reports/

    When --output is provided, it replaces that base directory.

    The final directory always remains:
        <base-output>/<project-name>/
    """

    if output_value is None:
        base_output_directory = (
            working_directory
            / "reports"
        )

    else:
        requested_output = Path(
            output_value
        ).expanduser()

        if requested_output.is_absolute():
            base_output_directory = (
                requested_output
            )

        else:
            base_output_directory = (
                working_directory
                / requested_output
            )

    return (
        base_output_directory
        / project_name
    ).resolve()


def output_location_is_scan_safe(
    *,
    project_path: Path,
    output_directory: Path,
    ignore: dict[str, list[str]],
) -> bool:
    """
    Check whether an output directory inside the scanned project is
    already covered by the current exact-name ignore rules.

    Path-aware output exclusion belongs to the shared scanner phase.
    Until then, an unignored in-project custom output path is rejected
    rather than allowing a later scan to ingest generated reports.
    """

    try:
        relative_output = (
            output_directory.relative_to(
                project_path
            )
        )
    except ValueError:
        return True

    if not relative_output.parts:
        return False

    top_level_directory = (
        relative_output.parts[0]
    )

    return (
        top_level_directory
        in ignore.get(
            "IGNORE_FOLDERS",
            [],
        )
    )


def run_analysis(
    *,
    project_value: str,
    architecture_requested: bool,
    report_requested: bool,
    output_value: str | None,
    working_directory: Path,
) -> int:
    """Run the migrated architecture/report analysis slice."""

    project_path = resolve_project_path(
        project_value
    )

    if not project_path.exists():
        print(
            "Error: project path does not exist: "
            f"{project_path}",
            file=sys.stderr,
        )
        return INVALID_INPUT

    if not project_path.is_dir():
        print(
            "Error: project path is not a directory: "
            f"{project_path}",
            file=sys.stderr,
        )
        return INVALID_INPUT

    project_name = (
        project_path.name
        or "root"
    )

    output_directory = (
        resolve_output_directory(
            output_value,
            project_name,
            working_directory,
        )
    )

    if (
        output_directory.exists()
        and not output_directory.is_dir()
    ):
        print(
            "Error: output path exists but is not "
            f"a directory: {output_directory}",
            file=sys.stderr,
        )
        return OUTPUT_ERROR

    try:
        ignore = load_ignore_config(
            project_path=project_path
        )
    except ConfigurationError as error:
        print(
            f"Error: configuration: {error}",
            file=sys.stderr,
        )
        return INVALID_INPUT

    if not output_location_is_scan_safe(
        project_path=project_path,
        output_directory=output_directory,
        ignore=ignore,
    ):
        print(
            "Error: output directory is inside the "
            "scanned project but is not covered by "
            "the current ignore rules. Use an output "
            "directory outside the project or beneath "
            "an ignored top-level directory such as "
            "`reports`.",
            file=sys.stderr,
        )
        return INVALID_INPUT

    print(
        f"Project: {project_path}"
    )
    print(
        f"Output directory: {output_directory}"
    )

    print(
        "\nScanning project..."
    )

    files = scan_project(
        str(
            project_path
        ),
        ignore,
    )

    print(
        "Scanned files after ignores: "
        f"{len(files)}"
    )

    if not files:
        print(
            "Warning: no files were found. "
            "Check the project path or ignore rules."
        )
        return 0

    try:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        print(
            "Error: could not create output "
            f"directory: {error}",
            file=sys.stderr,
        )
        return OUTPUT_ERROR

    if architecture_requested:
        architecture_output = (
            output_directory
            / (
                f"{project_name}"
                "-architecture.md"
            )
        )

        print(
            "\nGenerating architecture..."
        )

        architecture = build_architecture(
            str(
                project_path
            ),
            ignore,
        )

        try:
            architecture_output.write_text(
                "# Project Architecture\n\n"
                + architecture,
                encoding="utf-8",
                newline="\n",
            )
        except OSError as error:
            print(
                "Error: could not write "
                "architecture report: "
                f"{error}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR

        print(
            "Architecture written to: "
            f"{architecture_output}"
        )

    if report_requested:
        report_output = (
            output_directory
            / (
                f"{project_name}"
                "-project-report.md"
            )
        )

        print(
            "\nGenerating project report..."
        )

        try:
            build_report(
                project_path=str(
                    project_path
                ),
                file_paths=files,
                ignore=ignore,
                output_path=str(
                    report_output
                ),
            )
        except OSError as error:
            print(
                "Error: could not write "
                f"project report: {error}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR

        print(
            "Project report written to: "
            f"{report_output}"
        )

    print(
        "\nDone."
    )

    return 0
