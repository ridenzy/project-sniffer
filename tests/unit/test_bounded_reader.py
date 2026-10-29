from __future__ import annotations

import os
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


class BoundedReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.project = Path(
            self.temporary_directory.name
        )

    def tearDown(self) -> None:
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

    def test_oversized_text_file_is_classified_without_content(
        self,
    ) -> None:
        path = (
            self.project
            / "oversized.txt"
        )

        path.write_bytes(
            b"a" * 17
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "oversized.txt"
            ),
            max_source_bytes=16,
        )

        self.assertEqual(
            result.status,
            FileReadStatus.OVERSIZED,
        )

        self.assertIsNone(
            result.content
        )

        self.assertEqual(
            result.size_bytes,
            17,
        )

    def test_binary_classification_precedes_oversized_when_sample_has_nul(
        self,
    ) -> None:
        path = (
            self.project
            / "large-binary.dat"
        )

        path.write_bytes(
            b"ab\x00"
            + (b"x" * 20)
        )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "large-binary.dat"
            ),
            max_source_bytes=8,
        )

        self.assertEqual(
            result.status,
            FileReadStatus.BINARY,
        )

        self.assertEqual(
            result.size_bytes,
            23,
        )

    def test_manifest_reader_forwards_explicit_size_limit(
        self,
    ) -> None:
        path = (
            self.project
            / "manifest-large.txt"
        )

        path.write_bytes(
            b"123456789"
        )

        manifest = ScanManifest(
            project_path=self.project,
            directories=(),
            files=(
                self.scanned_file(
                    "manifest-large.txt"
                ),
            ),
        )

        results = read_manifest_files(
            manifest,
            max_source_bytes=8,
        )

        self.assertEqual(
            results[0].status,
            FileReadStatus.OVERSIZED,
        )

    def test_nonpositive_max_source_bytes_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            read_scanned_file(
                project_path=self.project,
                scanned_file=self.scanned_file(
                    "unused.txt"
                ),
                max_source_bytes=0,
            )

    def test_special_file_is_rejected_without_content_open(
        self,
    ) -> None:
        if not hasattr(
            os,
            "mkfifo",
        ):
            self.skipTest(
                "os.mkfifo is unavailable"
            )

        path = (
            self.project
            / "named-pipe"
        )

        try:
            os.mkfifo(
                path
            )
        except OSError as error:
            self.skipTest(
                "FIFO creation is unavailable: "
                f"{type(error).__name__}"
            )

        result = read_scanned_file(
            project_path=self.project,
            scanned_file=self.scanned_file(
                "named-pipe"
            ),
        )

        self.assertEqual(
            result.status,
            FileReadStatus.UNREADABLE,
        )

        self.assertEqual(
            result.error_type,
            "UnsupportedFileType",
        )


if __name__ == "__main__":
    unittest.main()
