from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_sniffer.scanning import (
    GitIgnoreMatcher,
)


class GitIgnoreMatcherTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.project = Path(
            self.temporary_directory.name
        )

    def tearDown(
        self,
    ) -> None:
        self.temporary_directory.cleanup()

    def test_missing_gitignore_leaves_paths_unmatched(
        self,
    ) -> None:
        matcher = GitIgnoreMatcher()

        matcher.load_directory(
            directory_path=self.project,
            relative_directory="",
        )

        self.assertFalse(
            matcher.matches_file(
                "src/app.py"
            )
        )

        self.assertFalse(
            matcher.matches_directory(
                "build"
            )
        )

    def test_root_gitignore_supports_paths_globs_and_negation(
        self,
    ) -> None:
        (
            self.project
            / ".gitignore"
        ).write_text(
            "/generated/\n"
            "*.tmp\n"
            "!keep.tmp\n",
            encoding="utf-8",
            newline="\n",
        )

        matcher = GitIgnoreMatcher()

        matcher.load_directory(
            directory_path=self.project,
            relative_directory="",
        )

        self.assertTrue(
            matcher.matches_directory(
                "generated"
            )
        )

        self.assertTrue(
            matcher.matches_file(
                "src/cache.tmp"
            )
        )

        self.assertFalse(
            matcher.matches_file(
                "src/keep.tmp"
            )
        )

    def test_nested_gitignore_overrides_parent_file_rule(
        self,
    ) -> None:
        (
            self.project
            / ".gitignore"
        ).write_text(
            "*.log\n",
            encoding="utf-8",
            newline="\n",
        )

        source = (
            self.project
            / "src"
        )

        source.mkdir()

        (
            source
            / ".gitignore"
        ).write_text(
            "!keep.log\n",
            encoding="utf-8",
            newline="\n",
        )

        matcher = GitIgnoreMatcher()

        matcher.load_directory(
            directory_path=self.project,
            relative_directory="",
        )

        matcher.load_directory(
            directory_path=source,
            relative_directory="src",
        )

        self.assertTrue(
            matcher.matches_file(
                "src/drop.log"
            )
        )

        self.assertFalse(
            matcher.matches_file(
                "src/keep.log"
            )
        )

        self.assertTrue(
            matcher.matches_file(
                "other/drop.log"
            )
        )

    def test_symlink_gitignore_is_not_followed(
        self,
    ) -> None:
        source_path = (
            self.project
            / ".gitignore"
        )

        source_path.write_text(
            "*.tmp\n",
            encoding="utf-8",
            newline="\n",
        )

        matcher = GitIgnoreMatcher()

        with patch.object(
            Path,
            "is_symlink",
            return_value=True,
        ):
            matcher.load_directory(
                directory_path=self.project,
                relative_directory="",
            )

        self.assertFalse(
            matcher.matches_file(
                "scratch.tmp"
            )
        )


if __name__ == "__main__":
    unittest.main()
