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
    CallResolutionStatus,
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

    def test_module_attribute_call_enters_call_index(
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

        call_index = build_call_index(
            graph
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
                    symbol="run",
                ),
            ),
        )

        self.assertEqual(
            tuple(
                entry.endpoint
                for entry
                in call_index.inbound
            ),
            (
                CallEndpoint(
                    path="pkg/worker.py",
                    symbol="module_execute",
                ),
            ),
        )


    def test_class_attribute_call_enters_call_index(
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

        call_index = build_call_index(
            graph
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
                    symbol="run",
                ),
            ),
        )

        self.assertEqual(
            tuple(
                entry.endpoint
                for entry
                in call_index.inbound
            ),
            (
                CallEndpoint(
                    path="pkg/app.py",
                    symbol="Worker.execute",
                ),
            ),
        )


    def test_local_instance_method_call_enters_call_index(
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

        call_index = build_call_index(
            graph
        )

        run_entry = next(
            entry
            for entry in call_index.outbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="run",
            )
        )

        self.assertIn(
            "Worker.execute",
            tuple(
                edge.target_symbol
                for edge in run_entry.edges
            ),
        )

        method_entry = next(
            entry
            for entry in call_index.inbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="Worker.execute",
            )
        )

        self.assertEqual(
            len(method_entry.edges),
            1,
        )

        self.assertEqual(
            method_entry.edges[0].scope,
            "run",
        )

        self.assertEqual(
            method_entry.edges[0].line,
            7,
        )


    def test_direct_class_method_local_instance_call_enters_call_index(
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

        call_index = build_call_index(
            graph
        )

        run_entry = next(
            entry
            for entry in call_index.outbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="Manager.run",
            )
        )

        self.assertIn(
            "Worker.execute",
            tuple(
                edge.target_symbol
                for edge in run_entry.edges
            ),
        )

        method_entry = next(
            entry
            for entry in call_index.inbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="Worker.execute",
            )
        )

        self.assertEqual(
            len(method_entry.edges),
            1,
        )

        self.assertEqual(
            method_entry.edges[0].scope,
            "Manager.run",
        )

        self.assertEqual(
            method_entry.edges[0].line,
            8,
        )


    def test_passive_gap_local_instance_call_enters_call_index(
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

        call_index = build_call_index(
            graph
        )

        run_entry = next(
            entry
            for entry in call_index.outbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="Manager.run",
            )
        )

        self.assertIn(
            "Worker.execute",
            tuple(
                edge.target_symbol
                for edge in run_entry.edges
            ),
        )

        method_entry = next(
            entry
            for entry in call_index.inbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="Worker.execute",
            )
        )

        self.assertEqual(
            len(method_entry.edges),
            1,
        )

        self.assertEqual(
            method_entry.edges[0].line,
            11,
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
                    "helper = replacement\n"
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

        call_index = build_call_index(
            graph
        )

        self.assertEqual(
            call_index.outbound,
            (),
        )

        self.assertEqual(
            call_index.inbound,
            (),
        )


    def test_same_file_one_hop_inherited_calls_enter_call_index(
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

        call_index = build_call_index(
            graph
        )

        class_entry = next(
            entry
            for entry in call_index.outbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="class_call",
            )
        )

        self.assertEqual(
            tuple(
                (
                    edge.target_symbol,
                    edge.line,
                )
                for edge in class_entry.edges
            ),
            (
                (
                    "Base.execute",
                    9,
                ),
            ),
        )

        instance_entry = next(
            entry
            for entry in call_index.outbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="instance_call",
            )
        )

        self.assertEqual(
            tuple(
                (
                    edge.target_symbol,
                    edge.line,
                )
                for edge in instance_entry.edges
            ),
            (
                (
                    "Worker",
                    12,
                ),
                (
                    "Base.execute",
                    13,
                ),
            ),
        )

        inherited_entry = next(
            entry
            for entry in call_index.inbound
            if entry.endpoint
            == CallEndpoint(
                path="pkg/app.py",
                symbol="Base.execute",
            )
        )

        self.assertEqual(
            tuple(
                (
                    edge.scope,
                    edge.line,
                )
                for edge in inherited_entry.edges
            ),
            (
                (
                    "class_call",
                    9,
                ),
                (
                    "instance_call",
                    13,
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
