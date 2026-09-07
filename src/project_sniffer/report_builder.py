from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from project_sniffer.reading import (
    FileReadResult,
    FileReadStatus,
)


OUTPUT_PATH = "reports/project-report.md"


def get_safe_markdown_fence(
    content: str,
) -> str:
    """
    Create a Markdown code fence that cannot be accidentally closed
    by backticks contained inside the source file.
    """

    longest_backtick_run = 0
    current_backtick_run = 0

    for char in content:
        if char == "`":
            current_backtick_run += 1

            longest_backtick_run = max(
                longest_backtick_run,
                current_backtick_run,
            )
        else:
            current_backtick_run = 0

    fence_length = max(
        3,
        longest_backtick_run + 1,
    )

    return "`" * fence_length


def add_text_safely(
    report_sections: list[str],
    relative_path: str,
    content: str,
) -> None:
    """
    Add already-read text content to the Markdown report safely.

    Files are read and classified before they reach this module. This builder
    owns Markdown rendering and output writing, not target-project file access.
    """

    report_sections.append(
        f"# `{relative_path}`\n\n"
    )

    max_chunk_size = 25000

    if not content.strip():
        report_sections.append(
            "[empty file]\n\n"
        )

        report_sections.append(
            "---\n\n"
        )

        return

    markdown_fence = get_safe_markdown_fence(
        content
    )

    report_sections.append(
        f"{markdown_fence}text\n"
    )

    for index in range(
        0,
        len(content),
        max_chunk_size,
    ):
        chunk = content[
            index:index + max_chunk_size
        ]

        report_sections.append(
            chunk
        )

    report_sections.append(
        f"\n{markdown_fence}\n\n"
    )

    report_sections.append(
        "---\n\n"
    )


def _unreadable_detail(
    result: FileReadResult,
) -> str:
    error_type = (
        result.error_type
        or "UnknownError"
    )

    if result.error_message:
        return (
            f"{error_type}: "
            f"{result.error_message}"
        )

    return error_type


def build_report(
    project_path: str | Path,
    read_results: Sequence[FileReadResult],
    output_path: str | Path = OUTPUT_PATH,
) -> None:
    """
    Generate a Markdown source report from safe-reader results.

    Ignore handling belongs to the shared discovery manifest. Target-project
    content is never opened here: this function only renders FileReadResult
    evidence and writes the generated Project Sniffer report.
    """

    project_root = (
        Path(
            project_path
        )
        .expanduser()
        .resolve()
    )

    project_name = (
        project_root.name
        or "root"
    )

    report_sections = [
        "# Project Report\n\n",
        f"**Project:** `{project_name}`\n\n",
        "---\n\n",
    ]

    added_files = 0

    # Ignore filtering occurs before the read phase. This compatibility count
    # is retained during the 0.x migration so existing report summaries keep
    # their established shape.
    skipped_ignored = 0

    skipped_binary = 0
    skipped_unreadable = 0
    skipped_symlink = 0
    skipped_unsafe_path = 0
    skipped_markdown_error = 0

    unsafe_statuses = {
        FileReadStatus.ESCAPED_SYMLINK,
        FileReadStatus.OUTSIDE_PROJECT,
        FileReadStatus.PATH_MISMATCH,
    }

    for result in read_results:
        relative_path = (
            result
            .scanned_file
            .relative_path
        )

        if (
            result.status
            is FileReadStatus.BINARY
        ):
            skipped_binary += 1

            print(
                f"[SKIP binary] "
                f"{relative_path}"
            )

            continue

        if (
            result.status
            is FileReadStatus.UNREADABLE
        ):
            skipped_unreadable += 1

            print(
                f"[SKIP unreadable] "
                f"{relative_path} -> "
                f"{_unreadable_detail(result)}"
            )

            continue

        if (
            result.status
            is FileReadStatus.SYMLINK
        ):
            skipped_symlink += 1

            print(
                f"[SKIP symlink] "
                f"{relative_path}"
            )

            continue

        if result.status in unsafe_statuses:
            skipped_unsafe_path += 1

            label = (
                result.status.value.replace(
                    "_",
                    "-",
                )
            )

            print(
                f"[SKIP {label}] "
                f"{relative_path}"
            )

            continue

        if (
            result.status
            is not FileReadStatus.TEXT
        ):
            skipped_unsafe_path += 1

            print(
                f"[SKIP invalid-read-status] "
                f"{relative_path} -> "
                f"{result.status!r}"
            )

            continue

        content = result.content

        if content is None:
            skipped_unreadable += 1

            print(
                f"[SKIP invalid-read-result] "
                f"{relative_path} -> "
                "TEXT result has no content"
            )

            continue

        try:
            add_text_safely(
                report_sections,
                relative_path,
                content,
            )

            added_files += 1

            print(
                f"[ADD] {relative_path}"
            )

        except Exception as error:
            skipped_markdown_error += 1

            print(
                f"[SKIP markdown-error] "
                f"{relative_path} -> "
                f"{type(error).__name__}: "
                f"{error}"
            )

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        "".join(
            report_sections
        ),
        encoding="utf-8",
        newline="\n",
    )

    print(
        "\nReport summary:"
    )
    print(
        f"  Added text files: "
        f"{added_files}"
    )
    print(
        f"  Skipped ignored files: "
        f"{skipped_ignored}"
    )
    print(
        f"  Skipped binary files: "
        f"{skipped_binary}"
    )
    print(
        f"  Skipped unreadable files: "
        f"{skipped_unreadable}"
    )
    print(
        f"  Skipped symlink files: "
        f"{skipped_symlink}"
    )
    print(
        f"  Skipped unsafe-path files: "
        f"{skipped_unsafe_path}"
    )
    print(
        f"  Skipped markdown-error files: "
        f"{skipped_markdown_error}"
    )
    print(
        f"  Report saved to: "
        f"{output}"
    )
