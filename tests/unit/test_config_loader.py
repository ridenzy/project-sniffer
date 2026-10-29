from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from project_sniffer.config.loader import (
    ConfigurationError,
    get_personal_registry_path,
    load_personal_ignores,
)


class PersonalRegistryLoaderTests(
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

        self.registry_path = (
            self.workspace
            / "personal_ignores.json"
        )

    def tearDown(
        self,
    ) -> None:
        self.temporary_directory.cleanup()

    def write_registry(
        self,
        data: object,
    ) -> None:
        self.registry_path.write_text(
            json.dumps(
                data,
                indent=4,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_legacy_global_shape_is_rejected(
        self,
    ) -> None:
        self.write_registry(
            {
                "IGNORE_FOLDERS": [
                    "storage",
                ],
                "IGNORE_FILES": [
                    "agents.json",
                ],
            }
        )

        with self.assertRaises(
            ConfigurationError
        ) as raised:
            load_personal_ignores(
                project_path=self.project,
                registry_path=self.registry_path,
            )

        self.assertIn(
            "schema-version-1 per-project format",
            str(
                raised.exception
            ),
        )

    def test_profile_id_matches_project_root_name(
        self,
    ) -> None:
        self.write_registry(
            {
                "schema_version": 1,
                "projects": {
                    "fixture-project": {
                        "IGNORE_FOLDERS": [
                            "storage",
                        ],
                        "IGNORE_FILES": [],
                    },
                    "another-project": {
                        "IGNORE_FOLDERS": [
                            "other",
                        ],
                        "IGNORE_FILES": [],
                    },
                },
            }
        )

        loaded = load_personal_ignores(
            project_path=self.project,
            registry_path=self.registry_path,
        )

        self.assertEqual(
            loaded[
                "IGNORE_FOLDERS"
            ],
            [
                "storage",
            ],
        )

    def test_root_name_can_match_alias_profile(
        self,
    ) -> None:
        self.write_registry(
            {
                "schema_version": 1,
                "projects": {
                    "company-a-frontend": {
                        "ROOT_NAME": (
                            "fixture-project"
                        ),
                        "IGNORE_FOLDERS": [
                            "coverage",
                        ],
                        "IGNORE_FILES": [],
                    },
                },
            }
        )

        loaded = load_personal_ignores(
            project_path=self.project,
            registry_path=self.registry_path,
        )

        self.assertEqual(
            loaded[
                "IGNORE_FOLDERS"
            ],
            [
                "coverage",
            ],
        )

    def test_root_path_profile_wins_over_name_only_profile(
        self,
    ) -> None:
        self.write_registry(
            {
                "schema_version": 1,
                "projects": {
                    "generic": {
                        "ROOT_NAME": (
                            "fixture-project"
                        ),
                        "IGNORE_FOLDERS": [
                            "generic-folder",
                        ],
                        "IGNORE_FILES": [],
                    },
                    "specific": {
                        "ROOT_NAME": (
                            "fixture-project"
                        ),
                        "ROOT_PATH": str(
                            self.project
                        ),
                        "IGNORE_FOLDERS": [
                            "specific-folder",
                        ],
                        "IGNORE_FILES": [],
                    },
                },
            }
        )

        loaded = load_personal_ignores(
            project_path=self.project,
            registry_path=self.registry_path,
        )

        self.assertEqual(
            loaded[
                "IGNORE_FOLDERS"
            ],
            [
                "specific-folder",
            ],
        )

    def test_nonmatching_registry_returns_empty_config(
        self,
    ) -> None:
        self.write_registry(
            {
                "schema_version": 1,
                "projects": {
                    "another-project": {
                        "IGNORE_FOLDERS": [
                            "storage",
                        ],
                        "IGNORE_FILES": [],
                    },
                },
            }
        )

        loaded = load_personal_ignores(
            project_path=self.project,
            registry_path=self.registry_path,
        )

        self.assertEqual(
            loaded,
            {
                "IGNORE_FOLDERS": [],
                "IGNORE_FILES": [],
            },
        )

    def test_ambiguous_same_specificity_profiles_are_rejected(
        self,
    ) -> None:
        self.write_registry(
            {
                "schema_version": 1,
                "projects": {
                    "first": {
                        "ROOT_NAME": (
                            "fixture-project"
                        ),
                        "IGNORE_FOLDERS": [],
                        "IGNORE_FILES": [],
                    },
                    "second": {
                        "ROOT_NAME": (
                            "fixture-project"
                        ),
                        "IGNORE_FOLDERS": [],
                        "IGNORE_FILES": [],
                    },
                },
            }
        )

        with self.assertRaises(
            ConfigurationError
        ):
            load_personal_ignores(
                project_path=self.project,
                registry_path=self.registry_path,
            )

    def test_invalid_schema_version_is_rejected(
        self,
    ) -> None:
        self.write_registry(
            {
                "schema_version": 2,
                "projects": {},
            }
        )

        with self.assertRaises(
            ConfigurationError
        ):
            load_personal_ignores(
                project_path=self.project,
                registry_path=self.registry_path,
            )

    def test_default_registry_lives_in_package_resources(
        self,
    ) -> None:
        path = get_personal_registry_path()

        self.assertEqual(
            path.name,
            "personal_ignores.json",
        )

        self.assertEqual(
            path.parent.name,
            "resources",
        )

        self.assertEqual(
            path.parent.parent.name,
            "project_sniffer",
        )


if __name__ == "__main__":
    unittest.main()
