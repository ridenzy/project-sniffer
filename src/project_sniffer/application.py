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
from project_sniffer.docs_reporter import (
    DocsReportError,
    build_documentation_reports,
    print_documentation_summary,
)
from project_sniffer.evidence import (
    build_source_evidence,
)
from project_sniffer.indexing import (
    build_semantic_project_index,
)
from project_sniffer.reading import (
    read_manifest_files,
)
from project_sniffer.report_builder import (
    build_report,
)
from project_sniffer.scanning import (
    ScanError,
    scan_project,
)
from project_sniffer.tracing import (
    build_dependency_graph,
    render_dependency_graph,
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

def _confirm_private_docs_ignore_override() -> bool:
    print(
        "\nWARNING: docs/private/ exists and is "
        "excluded by Project Sniffer ignore "
        "configuration."
    )

    print(
        "Generating this report may include "
        "private or sensitive project "
        "documentation."
    )

    print(
        "Only the docs/private/ scope exclusion "
        "will be overridden for this run. "
        "All other Project Sniffer ignore rules "
        "remain active."
    )

    while True:
        try:
            answer = input(
                "Generate the docs/private/ "
                "report? [y/N]: "
            )

        except EOFError:
            print(
                "\nNo interactive response was "
                "available. Keeping docs/private/ "
                "ignored."
            )
            return False

        normalized = (
            answer
            .strip()
            .lower()
        )

        if normalized in {
            "y",
            "yes",
        }:
            print(
                "Private documentation override "
                "approved for this run."
            )
            return True

        if normalized in {
            "",
            "n",
            "no",
        }:
            print(
                "Private documentation override "
                "declined. Keeping docs/private/ "
                "ignored."
            )
            return False

        print(
            "Please answer y or n."
        )

def run_analysis(
    *,
    project_value: str,
    architecture_requested: bool,
    report_requested: bool,
    trace_requested: bool,
    docs_requested: bool,
    output_value: str | None,
    working_directory: Path,
) -> int:
    """Run the implemented analysis and documentation-output operations."""

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

    if output_directory == project_path:
        print(
            "Error: output directory cannot be the "
            "project root itself.",
            file=sys.stderr,
        )
        return INVALID_INPUT

    print(
        f"Project: {project_path}"
    )
    print(
        f"Output directory: {output_directory}"
    )

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

    analysis_requested = (
        architecture_requested
        or report_requested
        or trace_requested
    )

    manifest = None

    if analysis_requested:
        print(
            "\nScanning project..."
        )

        try:
            manifest = scan_project(
                project_path,
                ignore,
                excluded_directories=(
                    output_directory,
                ),
            )
        except ScanError as error:
            print(
                f"Error: scan: {error}",
                file=sys.stderr,
            )
            return INVALID_INPUT

        print(
            "Scanned files after ignores: "
            f"{len(manifest.files)}"
        )

        if not manifest.files:
            print(
                "Warning: no files were found. "
                "Check the project path or ignore rules."
            )

            if not docs_requested:
                return 0

    source_evidence = ()

    if (
        manifest is not None
        and manifest.files
        and (
            report_requested
            or trace_requested
        )
    ):
        try:
            read_results = read_manifest_files(
                manifest
            )

            source_evidence = (
                build_source_evidence(
                    read_results
                )
            )

        except OSError as error:
            print(
                "Error: could not prepare "
                "source evidence: "
                f"{error}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR


    if (
        architecture_requested
        and manifest is not None
        and manifest.files
    ):
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
            manifest
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

    if (
        report_requested
        and manifest is not None
        and manifest.files
    ):
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
                project_path=project_path,
                source_evidence=source_evidence,
                output_path=report_output,
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

    if (
        trace_requested
        and manifest is not None
        and manifest.files
    ):
        trace_output = (
            output_directory
            / (
                f"{project_name}"
                "-trace.md"
            )
        )

        print(
            "\nGenerating dependency trace..."
        )

        semantic_index = (
            build_semantic_project_index(
                source_evidence
            )
        )

        dependency_graph = (
            build_dependency_graph(
                semantic_index
            )
        )

        trace_text = (
            render_dependency_graph(
                dependency_graph
            )
        )

        try:
            trace_output.write_text(
                trace_text,
                encoding="utf-8",
                newline="\n",
            )
        except OSError as error:
            print(
                "Error: could not write "
                "dependency trace: "
                f"{error}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR

        print(
            "Dependency trace written to: "
            f"{trace_output}"
        )


    if docs_requested:
        print(
            "\nGenerating documentation reports..."
        )

        try:
            docs_summary = (
                build_documentation_reports(
                    project_path=project_path,
                    output_directory=(
                        output_directory
                    ),
                    ignore=ignore,
                    confirm_private_ignore_override=(
                        _confirm_private_docs_ignore_override
                    ),
                )
            )
        except (
            DocsReportError,
            OSError,
        ) as error:
            print(
                "Error: documentation reports: "
                f"{error}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR

        print_documentation_summary(
            docs_summary
        )

    print(
        "\nDone."
    )

    return 0
