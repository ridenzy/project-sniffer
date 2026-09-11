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

    def test_resolved_internal_import_becomes_dependency_edge(
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
                .POTENTIAL_INTERNAL
            ),
        )

        self.assertEqual(
            len(
                graph.edges
            ),
            1,
        )

        edge = graph.edges[0]

        self.assertIs(
            edge.kind,
            DependencyKind.IMPORT,
        )

        self.assertEqual(
            edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_path,
            "pkg/worker.py",
        )

        self.assertEqual(
            edge.line,
            2,
        )

        self.assertEqual(
            edge.scope,
            "load",
        )

        self.assertIs(
            edge.resolution,
            graph.import_resolutions[0],
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
