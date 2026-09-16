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
    CallResolutionProof,
    CallResolutionStatus,
    DependencyKind,
    ImportResolutionStatus,
    build_dependency_graph,
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

    def test_resolved_module_attribute_call_becomes_dependency_edge(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "import pkg.worker as worker\n"
                    "\n"
                    "def run():\n"
                    "    return "
                    "worker.module_execute()\n"
                ),
            ),
            self.evidence(
                "pkg/worker.py",
                (
                    "def module_execute():\n"
                    "    return True\n"
                ),
            ),
        )

        call_edges = tuple(
            edge
            for edge in graph.edges
            if edge.kind
            is DependencyKind.CALL
        )

        self.assertEqual(
            len(
                call_edges
            ),
            1,
        )

        edge = call_edges[0]

        self.assertEqual(
            edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_path,
            "pkg/worker.py",
        )

        self.assertEqual(
            edge.target_symbol,
            "module_execute",
        )

        self.assertEqual(
            edge.scope,
            "run",
        )

        self.assertEqual(
            edge.line,
            4,
        )


    def test_same_file_class_attribute_call_becomes_dependency_edge(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    return "
                    "Worker.execute(None)\n"
                ),
            ),
        )

        call_edges = tuple(
            edge
            for edge in graph.edges
            if edge.kind
            is DependencyKind.CALL
        )

        self.assertEqual(
            len(
                call_edges
            ),
            1,
        )

        edge = call_edges[0]

        self.assertEqual(
            edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_symbol,
            "Worker.execute",
        )

        self.assertEqual(
            edge.scope,
            "run",
        )

        self.assertEqual(
            edge.line,
            6,
        )


    def test_local_instance_method_call_becomes_dependency_edge(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    worker = Worker()\n"
                    "    return worker.execute()\n"
                ),
            ),
        )

        method_edges = tuple(
            edge
            for edge in graph.edges
            if (
                edge.kind
                is DependencyKind.CALL
                and edge.target_symbol
                == "Worker.execute"
            )
        )

        self.assertEqual(
            len(method_edges),
            1,
        )

        edge = method_edges[0]

        self.assertEqual(
            edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.scope,
            "run",
        )

        self.assertEqual(
            edge.line,
            7,
        )


    def test_direct_class_method_local_instance_call_becomes_dependency_edge(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "class Manager:\n"
                    "    def run(self):\n"
                    "        worker = Worker()\n"
                    "        return worker.execute()\n"
                ),
            ),
        )

        method_edges = tuple(
            edge
            for edge in graph.edges
            if (
                edge.kind
                is DependencyKind.CALL
                and edge.target_symbol
                == "Worker.execute"
            )
        )

        self.assertEqual(
            len(method_edges),
            1,
        )

        edge = method_edges[0]

        self.assertEqual(
            edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.scope,
            "Manager.run",
        )

        self.assertEqual(
            edge.line,
            8,
        )


    def test_passive_gap_local_instance_call_becomes_dependency_edge(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "class Manager:\n"
                    "    def run(self):\n"
                    "        worker = Worker()\n"
                    "        count = 10\n"
                    "        label = \"ready\"\n"
                    "        pass\n"
                    "        return worker.execute()\n"
                ),
            ),
        )

        method_edges = tuple(
            edge
            for edge in graph.edges
            if (
                edge.kind
                is DependencyKind.CALL
                and edge.target_symbol
                == "Worker.execute"
            )
        )

        self.assertEqual(
            len(method_edges),
            1,
        )

        edge = method_edges[0]

        self.assertEqual(
            edge.scope,
            "Manager.run",
        )

        self.assertEqual(
            edge.line,
            11,
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

    def test_stable_same_file_call_becomes_dependency_edge(
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
                .RESOLVED_INTERNAL
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
            DependencyKind.CALL,
        )

        self.assertEqual(
            edge.source_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_path,
            "pkg/app.py",
        )

        self.assertEqual(
            edge.target_symbol,
            "helper",
        )

        self.assertEqual(
            edge.scope,
            "run",
        )

        self.assertEqual(
            edge.line,
            5,
        )

        self.assertIs(
            edge.resolution,
            graph.call_resolutions[0],
        )


    def test_same_file_one_hop_inherited_calls_become_dependency_edges(
        self,
    ) -> None:
        graph = self.graph(
            self.evidence(
                "pkg/app.py",
                (
                    "class Base:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "class Worker(Base):\n"
                    "    pass\n"
                    "\n"
                    "def class_call():\n"
                    "    return Worker.execute(None)\n"
                    "\n"
                    "def instance_call():\n"
                    "    worker = Worker()\n"
                    "    return worker.execute()\n"
                ),
            ),
        )

        inherited_edges = tuple(
            edge
            for edge in graph.edges
            if (
                edge.kind
                is DependencyKind.CALL
                and edge.target_symbol
                == "Base.execute"
            )
        )

        self.assertEqual(
            len(inherited_edges),
            2,
        )

        self.assertEqual(
            tuple(
                (
                    edge.source_path,
                    edge.target_path,
                    edge.scope,
                    edge.line,
                    edge.resolution.proof,
                )
                for edge in inherited_edges
            ),
            (
                (
                    "pkg/app.py",
                    "pkg/app.py",
                    "class_call",
                    9,
                    (
                        CallResolutionProof
                        .SAME_FILE_INHERITED_CLASS_ATTRIBUTE_BINDING
                    ),
                ),
                (
                    "pkg/app.py",
                    "pkg/app.py",
                    "instance_call",
                    13,
                    (
                        CallResolutionProof
                        .LOCAL_INSTANCE_INHERITED_METHOD_BINDING
                    ),
                ),
            ),
        )

        constructor_edges = tuple(
            edge
            for edge in graph.edges
            if (
                edge.kind
                is DependencyKind.CALL
                and edge.scope
                == "instance_call"
                and edge.target_symbol
                == "Worker"
            )
        )

        self.assertEqual(
            len(constructor_edges),
            1,
        )

        self.assertEqual(
            constructor_edges[0].line,
            12,
        )