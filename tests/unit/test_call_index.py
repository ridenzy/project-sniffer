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
    CallEndpoint,
    DependencyKind,
    build_call_index,
    build_dependency_graph,
)


class CallIndexTests(
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

        read_result = FileReadResult(
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
            read_result=read_result,
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

    def test_confirmed_calls_build_outbound_and_inbound_indexes(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker import Worker\n"
                    "first = Worker()\n"
                    "\n"
                    "def build():\n"
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

        call_index = build_call_index(
            graph
        )

        self.assertEqual(
            len(
                graph.edges
            ),
            3,
        )

        self.assertEqual(
            tuple(
                entry.endpoint
                for entry
                in call_index.outbound
            ),
            (
                CallEndpoint(
                    path="pkg/app.py",
                    symbol=None,
                ),
                CallEndpoint(
                    path="pkg/app.py",
                    symbol="build",
                ),
            ),
        )

        self.assertEqual(
            tuple(
                edge.line
                for entry
                in call_index.outbound
                for edge
                in entry.edges
            ),
            (
                2,
                5,
            ),
        )

        self.assertTrue(
            all(
                edge.kind
                is DependencyKind.CALL
                for entry
                in call_index.outbound
                for edge
                in entry.edges
            )
        )

        self.assertEqual(
            len(
                call_index.inbound
            ),
            1,
        )

        self.assertEqual(
            call_index.inbound[0].endpoint,
            CallEndpoint(
                path="pkg/worker.py",
                symbol="Worker",
            ),
        )

        self.assertEqual(
            tuple(
                edge.line
                for edge
                in call_index.inbound[0].edges
            ),
            (
                2,
                5,
            ),
        )

        self.assertIs(
            call_index.inbound[0].edges[0],
            call_index.outbound[0].edges[0],
        )

    def test_uncertain_calls_do_not_enter_call_index(
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

        call_index = build_call_index(
            graph
        )

        self.assertEqual(
            graph.edges,
            (),
        )

        self.assertEqual(
            call_index.outbound,
            (),
        )

        self.assertEqual(
            call_index.inbound,
            (),
        )


if __name__ == "__main__":
    unittest.main()
