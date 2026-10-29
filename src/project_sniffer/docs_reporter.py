from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from project_sniffer.config import (
    IgnoreConfig,
)
from project_sniffer.evidence import (
    build_source_evidence,
)
from project_sniffer.reading import (
    read_manifest_files,
)
from project_sniffer.report_builder import (
    ReportBuildSummary,
    build_report,
)
from project_sniffer.scanning import (
    IgnoreMatcher,
    ScanManifest,
    scan_project,
)


class DocsReportError(RuntimeError):
    """Raised when documentation reports cannot be built safely."""


@dataclass(frozen=True)
class DocumentationScopeSummary:
    scope_name: str
    source_label: str
    exists: bool
    ignored_by_config: bool
    ignore_overridden: bool
    report_path: Path | None
    report_summary: ReportBuildSummary | None


@dataclass(frozen=True)
class DocumentationReportsSummary:
    public: DocumentationScopeSummary
    private: DocumentationScopeSummary

    @property
    def generated_reports(
        self,
    ) -> int:
        return sum(
            item.report_summary is not None
            for item in (
                self.public,
                self.private,
            )
        )


def _assert_scope_path_safe(
    *,
    project_root: Path,
    scope_name: str,
) -> Path:
    current = project_root

    for part in (
        "docs",
        scope_name,
    ):
        current = (
            current
            / part
        )

        if current.is_symlink():
            raise DocsReportError(
                "documentation scope path must not "
                f"contain a symlink: {current}"
            )

    return current


def _validate_report_destination(
    report_path: Path,
) -> None:
    if report_path.is_symlink():
        raise DocsReportError(
            "documentation report output must not "
            f"be a symlink: {report_path}"
        )

    if (
        report_path.exists()
        and not report_path.is_file()
    ):
        raise DocsReportError(
            "documentation report output exists "
            "but is not a regular file: "
            f"{report_path}"
        )


def _scope_ignore_match(
    *,
    ignore: IgnoreConfig,
    source_label: str,
) -> str | None:
    matcher = IgnoreMatcher.from_config(
        ignore
    )

    parts = PurePosixPath(
        source_label
    ).parts

    current_parts: list[str] = []

    for part in parts:
        current_parts.append(
            part
        )

        relative_path = "/".join(
            current_parts
        )

        if matcher.matches_folder(
            part,
            relative_path,
        ):
            return relative_path

    return None


def _empty_manifest(
    scope_path: Path,
) -> ScanManifest:
    return ScanManifest(
        project_path=scope_path.resolve(),
        directories=(),
        files=(),
    )


def _build_scope_report(
    *,
    project_root: Path,
    project_name: str,
    output_directory: Path,
    ignore: IgnoreConfig,
    scope_name: str,
    confirm_private_ignore_override: (
        Callable[[], bool] | None
    ) = None,
) -> DocumentationScopeSummary:
    source_label = (
        f"docs/{scope_name}"
    )

    scope_path = (
        _assert_scope_path_safe(
            project_root=project_root,
            scope_name=scope_name,
        )
    )

    if not scope_path.exists():
        return DocumentationScopeSummary(
            scope_name=scope_name,
            source_label=source_label,
            exists=False,
            ignored_by_config=False,
            ignore_overridden=False,
            report_path=None,
            report_summary=None,
        )

    if not scope_path.is_dir():
        raise DocsReportError(
            "documentation scope exists but is "
            f"not a directory: {scope_path}"
        )

    report_path = (
        output_directory
        / (
            f"{project_name}-"
            f"{scope_name}-docs-report.md"
        )
    )

    matched_ignore_path = (
        _scope_ignore_match(
            ignore=ignore,
            source_label=source_label,
        )
    )

    ignored_by_config = (
        matched_ignore_path is not None
    )

    private_scope_ignore = (
        scope_name == "private"
        and matched_ignore_path
        == source_label
    )

    ignore_overridden = False

    if private_scope_ignore:
        if (
            confirm_private_ignore_override
            is not None
        ):
            ignore_overridden = (
                confirm_private_ignore_override()
            )

        if not ignore_overridden:
            _validate_report_destination(
                report_path
            )

            if report_path.exists():
                report_path.unlink()

            return DocumentationScopeSummary(
                scope_name=scope_name,
                source_label=source_label,
                exists=True,
                ignored_by_config=True,
                ignore_overridden=False,
                report_path=None,
                report_summary=None,
            )

    if (
        ignored_by_config
        and not ignore_overridden
    ):
        manifest = _empty_manifest(
            scope_path
        )

    else:
        manifest = scan_project(
            scope_path,
            ignore,
            excluded_directories=(
                output_directory,
            ),
            apply_gitignore=False,
            ignore_path_prefix=source_label,
        )

    read_results = read_manifest_files(
        manifest
    )

    source_evidence = (
        build_source_evidence(
            read_results
        )
    )

    _validate_report_destination(
        report_path
    )

    report_summary = build_report(
        project_path=project_root,
        source_evidence=source_evidence,
        output_path=report_path,
        report_title=(
            f"{scope_name.title()} "
            "Documentation Report"
        ),
        project_name=project_name,
        source_root_label=(
            f"{source_label}/"
        ),
        print_summary=False,
    )

    return DocumentationScopeSummary(
        scope_name=scope_name,
        source_label=source_label,
        exists=True,
        ignored_by_config=ignored_by_config,
        ignore_overridden=ignore_overridden,
        report_path=report_path,
        report_summary=report_summary,
    )


def build_documentation_reports(
    *,
    project_path: Path,
    output_directory: Path,
    ignore: IgnoreConfig,
    confirm_private_ignore_override: (
        Callable[[], bool] | None
    ) = None,
) -> DocumentationReportsSummary:
    project_root = (
        project_path
        .expanduser()
        .resolve()
    )

    project_name = (
        project_root.name
        or "root"
    )

    public_summary = (
        _build_scope_report(
            project_root=project_root,
            project_name=project_name,
            output_directory=output_directory,
            ignore=ignore,
            scope_name="public",
        )
    )

    private_summary = (
        _build_scope_report(
            project_root=project_root,
            project_name=project_name,
            output_directory=output_directory,
            ignore=ignore,
            scope_name="private",
            confirm_private_ignore_override=(
                confirm_private_ignore_override
            ),
        )
    )

    return DocumentationReportsSummary(
        public=public_summary,
        private=private_summary,
    )


def print_documentation_summary(
    summary: DocumentationReportsSummary,
) -> None:
    print(
        "\nDocumentation report summary:"
    )

    for item in (
        summary.public,
        summary.private,
    ):
        print(
            f"  {item.source_label}/: "
            + (
                "found"
                if item.exists
                else "not found"
            )
        )

        if not item.exists:
            print(
                "    Report: not generated"
            )
            continue

        if item.ignore_overridden:
            print(
                "    Project Sniffer ignore policy: "
                "private-scope exclusion overridden "
                "for this run"
            )

        elif item.ignored_by_config:
            print(
                "    Project Sniffer ignore policy: "
                "entire scope excluded"
            )

        report_summary = (
            item.report_summary
        )

        if report_summary is None:
            print(
                "    Report: not generated"
            )
            continue

        print(
            "    Added text files: "
            f"{report_summary.added_files}"
        )
        print(
            "    Skipped binary files: "
            f"{report_summary.skipped_binary_files}"
        )
        print(
            "    Skipped oversized files: "
            f"{report_summary.skipped_oversized_files}"
        )
        print(
            "    Skipped unreadable files: "
            f"{report_summary.skipped_unreadable_files}"
        )
        print(
            "    Skipped symlink files: "
            f"{report_summary.skipped_symlink_files}"
        )
        print(
            "    Skipped unsafe-path files: "
            f"{report_summary.skipped_unsafe_path_files}"
        )
        print(
            "    Skipped markdown-error files: "
            f"{report_summary.skipped_markdown_error_files}"
        )
        print(
            f"    Report: "
            f"{report_summary.output_path}"
        )

    print(
        "  Documentation reports generated: "
        f"{summary.generated_reports}"
    )
