from __future__ import annotations

import unittest
from pathlib import Path

from project_sniffer.evidence import (
    SourceEvidence,
    SourceLanguage,
)
from project_sniffer.indexing import (
    build_semantic_project_index,
)
from project_sniffer.reading import (
    FileReadResult,
    FileReadStatus,
)
from project_sniffer.scanning import (
    ScannedFile,
)
from project_sniffer.tracing import (
    ImportResolutionStatus,
    resolve_python_imports,
)


class PythonImportResolutionTests(
    unittest.TestCase
):
    def evidence(
        self,
        relative_path: str,
        content: str,
    ) -> SourceEvidence:
        scanned_file = ScannedFile(
            absolute_path=(
                Path("/tmp/project")
                / relative_path
            ),
            relative_path=relative_path,
        )

        result = FileReadResult(
            scanned_file=scanned_file,
            status=FileReadStatus.TEXT,
            content=content,
            resolved_path=(
                scanned_file.absolute_path
            ),
            size_bytes=len(
                content.encode(
                    "utf-8"
                )
            ),
            is_symlink=False,
        )

        return SourceEvidence(
            read_result=result,
            language=SourceLanguage.PYTHON,
        )

    def resolve(
        self,
        *evidence: SourceEvidence,
    ):
        index = (
            build_semantic_project_index(
                evidence
            )
        )

        return resolve_python_imports(
            index
        )

    def test_relative_import_resolves_internal_file(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker "
                    "import Worker\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertEqual(
            len(
                resolutions
            ),
            1,
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertEqual(
            resolution.requested_modules,
            (
                "pkg.worker",
            ),
        )

        self.assertEqual(
            resolution.target_path,
            "pkg/worker.py",
        )

    def test_absolute_import_resolves_internal_file(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from pkg.worker "
                    "import Worker\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertEqual(
            resolutions[0].target_path,
            "pkg/worker.py",
        )

    def test_src_layout_alias_resolves(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "src/project_sniffer/app.py",
                (
                    "from "
                    "project_sniffer.evidence "
                    "import SourceEvidence\n"
                ),
            ),
            self.evidence(
                (
                    "src/project_sniffer/"
                    "evidence/__init__.py"
                ),
                "class SourceEvidence:\n    pass\n",
            ),
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertEqual(
            resolutions[0].target_path,
            (
                "src/project_sniffer/"
                "evidence/__init__.py"
            ),
        )

    def test_unresolved_import_is_not_called_external(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                "import definitely_unknown\n",
            ),
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .UNRESOLVED
            ),
        )

        self.assertIsNone(
            resolutions[0].target_path
        )

    def test_duplicate_module_identity_is_ambiguous(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "consumer.py",
                "import foo\n",
            ),
            self.evidence(
                "foo.py",
                "VALUE = 1\n",
            ),
            self.evidence(
                "src/foo.py",
                "VALUE = 2\n",
            ),
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .AMBIGUOUS
            ),
        )

        self.assertEqual(
            resolutions[0].candidate_paths,
            (
                "foo.py",
                "src/foo.py",
            ),
        )

    def test_root_relative_import_is_invalid(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "app.py",
                "from .worker import Worker\n",
            ),
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .INVALID_RELATIVE_IMPORT
            ),
        )

    def test_parent_relative_import_resolves_from_nested_package(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/sub/app.py",
                (
                    "from ..worker "
                    "import Worker\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertEqual(
            len(
                resolutions
            ),
            1,
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertEqual(
            resolutions[0].requested_modules,
            (
                "pkg.worker",
            ),
        )

        self.assertEqual(
            resolutions[0].target_path,
            "pkg/worker.py",
        )

    def test_relative_import_beyond_top_level_is_invalid(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from ..worker "
                    "import Worker\n"
                ),
            ),
            self.evidence(
                "worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertEqual(
            len(
                resolutions
            ),
            1,
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            (
                ImportResolutionStatus
                .INVALID_RELATIVE_IMPORT
            ),
        )

        self.assertEqual(
            resolution.requested_modules,
            (),
        )

        self.assertIsNone(
            resolution.target_path
        )

        self.assertEqual(
            resolution.candidate_paths,
            (),
        )

    def test_src_source_root_is_not_relative_package_parent(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "src/pkg/app.py",
                (
                    "from ..worker "
                    "import Worker\n"
                ),
            ),
            self.evidence(
                "src/worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertEqual(
            len(
                resolutions
            ),
            1,
        )

        self.assertIs(
            resolutions[0].status,
            (
                ImportResolutionStatus
                .INVALID_RELATIVE_IMPORT
            ),
        )

        self.assertIsNone(
            resolutions[0].target_path
        )


if __name__ == "__main__":
    unittest.main()
