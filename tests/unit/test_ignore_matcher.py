from __future__ import annotations

import unittest

from project_sniffer.scanning import (
    IgnoreMatcher,
)


class IgnoreMatcherTests(
    unittest.TestCase
):
    def test_exact_and_glob_folder_rules_match(
        self,
    ) -> None:
        matcher = IgnoreMatcher.from_config(
            {
                "IGNORE_FOLDERS": [
                    "node_modules",
                    "*.egg-info",
                ],
                "IGNORE_FILES": [],
            }
        )

        self.assertTrue(
            matcher.matches_folder(
                "node_modules"
            )
        )

        self.assertTrue(
            matcher.matches_folder(
                "project_sniffer.egg-info"
            )
        )

        self.assertFalse(
            matcher.matches_folder(
                "src"
            )
        )

    def test_exact_and_glob_file_rules_match(
        self,
    ) -> None:
        matcher = IgnoreMatcher.from_config(
            {
                "IGNORE_FOLDERS": [],
                "IGNORE_FILES": [
                    "agents.json",
                    "*.bak",
                ],
            }
        )

        self.assertTrue(
            matcher.matches_file(
                "agents.json"
            )
        )

        self.assertTrue(
            matcher.matches_file(
                "settings.bak"
            )
        )

        self.assertFalse(
            matcher.matches_file(
                "settings.json"
            )
        )


    def test_project_relative_folder_rule_matches_only_intended_path(
        self,
    ) -> None:
        matcher = IgnoreMatcher.from_config(
            {
                "IGNORE_FOLDERS": [
                    "docs/private",
                ],
                "IGNORE_FILES": [],
            }
        )

        self.assertTrue(
            matcher.matches_folder(
                "private",
                "docs/private",
            )
        )

        self.assertFalse(
            matcher.matches_folder(
                "private",
                "src/docs/private",
            )
        )

    def test_root_anchored_file_rule_matches_only_project_root(
        self,
    ) -> None:
        matcher = IgnoreMatcher.from_config(
            {
                "IGNORE_FOLDERS": [],
                "IGNORE_FILES": [
                    "/project.local.json",
                ],
            }
        )

        self.assertTrue(
            matcher.matches_file(
                "project.local.json",
                "project.local.json",
            )
        )

        self.assertFalse(
            matcher.matches_file(
                "project.local.json",
                "config/project.local.json",
            )
        )


if __name__ == "__main__":
    unittest.main()
