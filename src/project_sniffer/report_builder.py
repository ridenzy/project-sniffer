from __future__ import annotations

import os

from project_sniffer.scanning import IgnoreMatcher


OUTPUT_PATH = "reports/project-report.md"


def is_valid_xml_char(char: str) -> bool:
    """
    XML 1.0 valid character ranges.

    This validation is retained from the DOCX report builder so that
    control characters and other unsafe characters are still removed
    from generated reports.
    """

    codepoint = ord(char)

    return (
        codepoint == 0x09
        or codepoint == 0x0A
        or codepoint == 0x0D
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def clean_text(text: str) -> str:
    """
    Remove every character that is not safe for the generated report.
    """

    return "".join(
        char
        for char in text
        if is_valid_xml_char(char)
    )


def is_binary(file_path):
    """
    Detect whether a file is binary.

    An unreadable file is not classified as binary here. The later text-read
    stage owns unreadable-file handling so that it can record the file in the
    correct report-summary category.
    """

    try:
        with open(
            file_path,
            "rb",
        ) as file_handle:
            chunk = file_handle.read(
                2048
            )

        return b"\x00" in chunk

    except OSError:
        return False


def should_skip_file(
    path,
    project_path,
    ignore,
):
    """
    Decide whether a file should be skipped using the shared ignore matcher.
    """

    matcher = IgnoreMatcher.from_config(
        ignore
    )

    relative_path = os.path.relpath(
        path,
        start=project_path,
    )

    path_parts = relative_path.split(
        os.sep
    )

    filename = os.path.basename(
        path
    )

    if matcher.matches_file(
        filename
    ):
        return True

    for part in path_parts[:-1]:
        if matcher.matches_folder(
            part
        ):
            return True

    return False


def get_safe_markdown_fence(content):
    """
    Create a Markdown code fence that cannot be accidentally closed
    by backticks contained inside the source file.

    For example, if the file contains three consecutive backticks,
    the generated report will use four or more backticks around it.
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
    report_sections,
    relative_path,
    content,
):
    """
    Add file content to the Markdown report safely.

    If a file is very large, split it into chunks so the report builder
    does not create one massive in-memory string section.
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


def build_report(
    project_path,
    file_paths,
    ignore=None,
    output_path=OUTPUT_PATH,
):
    """
    Generate a Markdown document containing readable project source files.

    This version is crash-resistant:

    - skips ignored files
    - skips binary files
    - cleans invalid control characters
    - skips only the problematic file if Markdown insertion fails
    - prints exactly which files were added/skipped
    """

    ignore = ignore or {}

    project_path = os.path.abspath(
        project_path
    )

    project_name = os.path.basename(
        project_path
    )

    report_sections = []

    report_sections.append(
        "# Project Report\n\n"
    )

    report_sections.append(
        f"**Project:** `{project_name}`\n\n"
    )

    report_sections.append(
        "---\n\n"
    )

    added_files = 0
    skipped_ignored = 0
    skipped_binary = 0
    skipped_unreadable = 0
    skipped_markdown_error = 0

    for path in file_paths:
        relative_path = os.path.relpath(
            path,
            start=project_path,
        )

        if should_skip_file(
            path,
            project_path,
            ignore,
        ):
            skipped_ignored += 1
            continue

        if is_binary(
            path
        ):
            skipped_binary += 1

            print(
                f"[SKIP binary] {relative_path}"
            )

            continue

        try:
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file_handle:
                content = file_handle.read()

            content = clean_text(
                content
            )

        except Exception as error:
            skipped_unreadable += 1

            print(
                f"[SKIP unreadable] "
                f"{relative_path} -> {error}"
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
                f"{relative_path} -> {error}"
            )

            continue

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:
        os.makedirs(
            output_directory,
            exist_ok=True,
        )

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as report_file:
        report_file.writelines(
            report_sections
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
        f"  Skipped markdown-error files: "
        f"{skipped_markdown_error}"
    )

    print(
        f"  Report saved to: "
        f"{output_path}"
    )
