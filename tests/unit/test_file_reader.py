from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from project_sniffer.reading import (
    FileReadStatus,
    read_manifest_files,
    read_scanned_file,
)
from project_sniffer.scanning.models import (
    ScanManifest,
    ScannedFile,
)


class SafeFileReaderTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.workspace = Path(
            self.temporary_directory.name
        )

        self.project = (
            self.workspace
            / "fixture-project"
        )

        self.project.mkdir()

    def tearDown(
        self,
    ) -> None:
        self.temporary_directory.cleanup()

    def scanned_file(
        self,
        relative_path: str,
    ) -> ScannedFile:
        return ScannedFile(
            absolute_path=(
                self.project
                / relative_path
            ),
            relative_path=relative_path,
        )

    def create_symlink_or_skip(
        self,
        *,
        target: Path,
        link: Path,
    ) -> None:
        try:
            link.symlink_to(
                target
            )
        except (
            OSError,
            NotImplementedError,
        ) as error:
            self.skipTest(
                "symlink creation is unavailable: "
                f"{type(error).__name__}"
            )

    def test_text_file_is_read_once_and_cleaned(
        self,
    ) -> None:
        path = (
            self.project
            / "app.txt"
        )

        path.write_text(
            "hello\x01world\n",
            encoding="utf-8",
            newline="\n",
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "app.txt"
            ),
        )

        self.assertEqual(
            result.status,
            FileReadStatus.TEXT,
        )

        self.assertEqual(
            result.content,
            "helloworld\n",
        )

        self.assertEqual(
            result.size_bytes,
            len(
                "hello\x01world\n".encode(
                    "utf-8"
                )
            ),
        )

    def test_binary_file_is_classified_without_text_content(
        self,
    ) -> None:
        path = (
            self.project
            / "binary.dat"
        )

        path.write_bytes(
            b"abc\x00def"
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "binary.dat"
            ),
        )

        self.assertEqual(
            result.status,
            FileReadStatus.BINARY,
        )

        self.assertIsNone(
            result.content
        )

    def test_internal_file_symlink_is_not_followed(
        self,
    ) -> None:
        target = (
            self.project
            / "target.txt"
        )

        target.write_text(
            "internal target\n",
            encoding="utf-8",
            newline="\n",
        )

        link = (
            self.project
            / "link.txt"
        )

        self.create_symlink_or_skip(
            target=target,
            link=link,
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "link.txt"
            ),
        )

        self.assertEqual(
            result.status,
            FileReadStatus.SYMLINK,
        )

        self.assertTrue(
            result.is_symlink
        )

        self.assertIsNone(
            result.content
        )

    def test_external_file_symlink_is_classified_as_escape(
        self,
    ) -> None:
        target = (
            self.workspace
            / "outside.txt"
        )

        target.write_text(
            "outside secret\n",
            encoding="utf-8",
            newline="\n",
        )

        link = (
            self.project
            / "outside-link.txt"
        )

        self.create_symlink_or_skip(
            target=target,
            link=link,
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "outside-link.txt"
            ),
        )

        self.assertEqual(
            result.status,
            (
                FileReadStatus
                .ESCAPED_SYMLINK
            ),
        )

        self.assertIsNone(
            result.content
        )

    def test_missing_file_is_unreadable(
        self,
    ) -> None:
        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "missing.txt"
            ),
        )

        self.assertEqual(
            result.status,
            FileReadStatus.UNREADABLE,
        )

        self.assertEqual(
            result.error_type,
            "FileNotFoundError",
        )

        self.assertIsNotNone(
            result.error_message
        )

    def test_absolute_path_outside_project_is_rejected(
        self,
    ) -> None:
        outside = (
            self.workspace
            / "outside.txt"
        )

        outside.write_text(
            "outside\n",
            encoding="utf-8",
            newline="\n",
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=ScannedFile(
                absolute_path=outside,
                relative_path="outside.txt",
            ),
        )

        self.assertEqual(
            result.status,
            (
                FileReadStatus
                .OUTSIDE_PROJECT
            ),
        )

        self.assertIsNone(
            result.content
        )

    def test_relative_path_mismatch_is_rejected(
        self,
    ) -> None:
        path = (
            self.project
            / "actual.txt"
        )

        path.write_text(
            "actual\n",
            encoding="utf-8",
            newline="\n",
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=ScannedFile(
                absolute_path=path,
                relative_path="different.txt",
            ),
        )

        self.assertEqual(
            result.status,
            FileReadStatus.PATH_MISMATCH,
        )

        self.assertIsNone(
            result.content
        )

    def test_manifest_reader_preserves_manifest_order(
        self,
    ) -> None:
        first = (
            self.project
            / "first.txt"
        )

        second = (
            self.project
            / "second.txt"
        )

        first.write_text(
            "first\n",
            encoding="utf-8",
            newline="\n",
        )

        second.write_text(
            "second\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = ScanManifest(
            project_path=self.project,
            directories=(),
            files=(
                self.scanned_file(
                    "second.txt"
                ),
                self.scanned_file(
                    "first.txt"
                ),
            ),
        )

        results = read_manifest_files(
            manifest
        )

        self.assertEqual(
            tuple(
                result.scanned_file.relative_path
                for result in results
            ),
            (
                "second.txt",
                "first.txt",
            ),
        )


if __name__ == "__main__":
    unittest.main()
