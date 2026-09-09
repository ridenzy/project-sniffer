from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from project_sniffer.docs_exporter import (
    DocsExportError,
    export_public_docs,
)
from project_sniffer.scanning import (
    ScanManifest,
    ScannedFile,
)


class DocsExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.workspace = Path(
            self.temporary_directory.name
        )

        self.project = (
            self.workspace
            / "project"
        )

        self.output = (
            self.workspace
            / "output"
        )

        self.project.mkdir()
        self.output.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def manifest_for(
        self,
        relative_path: str,
    ) -> ScanManifest:
        return ScanManifest(
            project_path=self.project,
            directories=(),
            files=(
                ScannedFile(
                    absolute_path=(
                        self.project
                        / relative_path
                    ),
                    relative_path=relative_path,
                ),
            ),
        )

    def test_file_symlink_is_not_followed(
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

        link = (
            self.project
            / "docs"
            / "public"
            / "link.txt"
        )

        link.parent.mkdir(
            parents=True
        )

        try:
            link.symlink_to(
                outside
            )
        except (
            OSError,
            NotImplementedError,
        ) as error:
            self.skipTest(
                "symlink creation is unavailable: "
                f"{type(error).__name__}"
            )

        summary = export_public_docs(
            manifest=self.manifest_for(
                "docs/public/link.txt"
            ),
            output_directory=self.output,
        )

        self.assertEqual(
            summary.copied_files,
            0,
        )

        self.assertEqual(
            summary.skipped_symlink_files,
            1,
        )

        self.assertFalse(
            (
                self.output
                / "docs"
                / "public"
                / "link.txt"
            ).exists()
        )

    def test_output_docs_symlink_is_rejected(
        self,
    ) -> None:
        source = (
            self.project
            / "docs"
            / "public"
            / "guide.md"
        )

        source.parent.mkdir(
            parents=True
        )

        source.write_text(
            "guide\n",
            encoding="utf-8",
            newline="\n",
        )

        outside_output = (
            self.workspace
            / "outside-output"
        )

        outside_output.mkdir()

        docs_link = (
            self.output
            / "docs"
        )

        try:
            docs_link.symlink_to(
                outside_output,
                target_is_directory=True,
            )
        except (
            OSError,
            NotImplementedError,
        ) as error:
            self.skipTest(
                "symlink creation is unavailable: "
                f"{type(error).__name__}"
            )

        with self.assertRaises(
            DocsExportError
        ):
            export_public_docs(
                manifest=self.manifest_for(
                    "docs/public/guide.md"
                ),
                output_directory=self.output,
            )


if __name__ == "__main__":
    unittest.main()
