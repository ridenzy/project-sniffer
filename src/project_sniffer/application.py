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
from project_sniffer.docs_exporter import (
    DocsExportError,
    export_public_docs,
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



def run_analysis(
    *,
    project_value: str,
    architecture_requested: bool,
    report_requested: bool,
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
            read_results = read_manifest_files(
                manifest
            )

            build_report(
                project_path=project_path,
                read_results=read_results,
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

    if docs_requested:
        docs_output = (
            output_directory
            / "docs"
            / "public"
        )

        print(
            "\nCopying public documentation..."
        )

        try:
            docs_summary = export_public_docs(
                manifest=manifest,
                output_directory=output_directory,
            )
        except DocsExportError as error:
            print(
                "Error: documentation export: "
                f"{error}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR

        print("Documentation copy summary:")
        print(
            f"  Copied files: "
            f"{docs_summary.copied_files}"
        )
        print(
            "  Skipped symlink files: "
            f"{docs_summary.skipped_symlink_files}"
        )
        print(
            "  Skipped unsafe-path files: "
            f"{docs_summary.skipped_unsafe_files}"
        )
        print(
            "  Skipped unreadable files: "
            f"{docs_summary.skipped_unreadable_files}"
        )

        if docs_summary.copied_files:
            print(
                "Documentation copied to: "
                f"{docs_output}"
            )
        else:
            print(
                "Documentation copy found no "
                "manifest-approved docs/public files."
            )

    print(
        "\nDone."
    )

    return 0
