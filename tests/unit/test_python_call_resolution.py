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
    CallResolutionStatus,
    resolve_python_calls,
    resolve_python_imports,
)


class PythonCallResolutionTests(
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

        import_resolutions = (
            resolve_python_imports(
                index
            )
        )

        return resolve_python_calls(
            index,
            import_resolutions,
        )

    def test_same_file_top_level_symbol_is_potential_candidate(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            ),
        )

        self.assertEqual(
            len(
                resolution.candidate_targets
            ),
            1,
        )

        target = (
            resolution
            .candidate_targets[0]
        )

        self.assertEqual(
            target.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            target.qualified_name,
            "helper",
        )

    def test_resolved_imported_symbol_is_potential_candidate(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker import Worker\n"
                    "\n"
                    "def run():\n"
                    "    return Worker()\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                (
                    "class Worker:\n"
                    "    pass\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            ),
        )

        target = (
            resolution
            .candidate_targets[0]
        )

        self.assertEqual(
            target.source_path,
            "pkg/worker.py",
        )

        self.assertEqual(
            target.qualified_name,
            "Worker",
        )

    def test_import_alias_is_used_as_call_binding(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker "
                    "import Worker as W\n"
                    "\n"
                    "def run():\n"
                    "    return W()\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                (
                    "class Worker:\n"
                    "    pass\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            ),
        )

        self.assertEqual(
            (
                resolution
                .candidate_targets[0]
                .qualified_name
            ),
            "Worker",
        )

    def test_multiple_internal_candidates_are_ambiguous(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker import Worker\n"
                    "\n"
                    "def Worker():\n"
                    "    return None\n"
                    "\n"
                    "def run():\n"
                    "    return Worker()\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                (
                    "class Worker:\n"
                    "    pass\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.AMBIGUOUS,
        )

        self.assertEqual(
            len(
                resolution.candidate_targets
            ),
            2,
        )

    def test_attribute_call_remains_unresolved(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def run(service):\n"
                    "    return service.execute()\n"
                ),
            ),
        )

        self.assertIs(
            resolutions[0].status,
            CallResolutionStatus.UNRESOLVED,
        )

        self.assertEqual(
            resolutions[0].candidate_targets,
            (),
        )

    def test_dynamic_call_remains_dynamic(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def run(callbacks):\n"
                    "    return callbacks[0]()\n"
                ),
            ),
        )

        self.assertIs(
            resolutions[0].status,
            CallResolutionStatus.DYNAMIC,
        )

        self.assertEqual(
            resolutions[0].candidate_targets,
            (),
        )


if __name__ == "__main__":
    unittest.main()
