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
    DependencyKind,
    ImportResolutionStatus,
    build_dependency_graph,
    CallResolutionStatus,
)


class DependencyGraphTests(
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

    def graph(
        self,
        *evidence: SourceEvidence,
    ):
        index = (
            build_semantic_project_index(
                evidence
            )
        )

        return build_dependency_graph(
            index
        )

    def test_resolved_import_and_call_become_dependency_edges(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "def load():\n"
                    "    from .worker import Worker\n"
                    "    return Worker()\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertEqual(
            graph.nodes,
            (
                "pkg/app.py",
                "pkg/worker.py",
            ),
        )

        self.assertEqual(
            len(
                graph.import_resolutions
            ),
            1,
        )

        self.assertEqual(
            len(
                graph.call_resolutions
            ),
            1,
        )

        self.assertIs(
            graph.call_resolutions[0].status,
            (
                CallResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertEqual(
            len(
                graph.edges
            ),
            2,
        )

        import_edge = graph.edges[0]
        call_edge = graph.edges[1]

        self.assertIs(
            call_edge.kind,
            DependencyKind.CALL,
        )

        self.assertEqual(
            call_edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            call_edge.target_path,
            "pkg/worker.py",
        )

        self.assertEqual(
            call_edge.target_symbol,
            "Worker",
        )

        self.assertEqual(
            call_edge.line,
            3,
        )

        self.assertEqual(
            call_edge.scope,
            "load",
        )

        self.assertIs(
            call_edge.resolution,
            graph.call_resolutions[0],
        )

    def test_uncertain_imports_remain_without_edges(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "import missing_dependency\n"
                    "from ..worker import Worker\n"
                ),
            ),
            self.evidence(
                "worker.py",
                "class Worker:\n    pass\n",
            ),
        )

        self.assertEqual(
            tuple(
                resolution.status
                for resolution
                in graph.import_resolutions
            ),
            (
                ImportResolutionStatus.UNRESOLVED,
                (
                    ImportResolutionStatus
                    .INVALID_RELATIVE_IMPORT
                ),
            ),
        )

        self.assertEqual(
            graph.edges,
            (),
        )

    def test_potential_same_file_call_does_not_become_edge(
        self,
    ) -> None:
        graph = self.graph(
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

        self.assertEqual(
            len(
                graph.call_resolutions
            ),
            1,
        )

        self.assertIs(
            graph.call_resolutions[0].status,
            (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            ),
        )

        self.assertEqual(
            graph.edges,
            (),
        )
