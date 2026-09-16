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
    build_dependency_graph,
    render_dependency_graph,
)


class TraceRendererTests(
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
            resolved_path=scanned_file.absolute_path,
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

    def test_renderer_preserves_confirmed_and_uncertain_evidence(
        self,
    ) -> None:
        index = build_semantic_project_index(
            (
                self.evidence(
                    "pkg/app.py",
                    (
                        "from .worker import Worker\n"
                        "import missing_dependency\n"
                        "\n"
                        "def build():\n"
                        "    return Worker()\n"
                        "\n"
                        "def shadowed(Worker):\n"
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
        )

        graph = build_dependency_graph(
            index
        )

        rendered = render_dependency_graph(
            graph
        )

        self.assertIn(
            "- Potential internal calls: 0",
            rendered,
        )

        self.assertIn(
            (
                "[IMPORT] "
                "`pkg/app.py` "
                "→ `pkg/worker.py`"
            ),
            rendered,
        )

        self.assertIn(
            (
                "[CALL] "
                "`pkg/app.py::build` "
                "→ "
                "`pkg/worker.py::Worker`"
            ),
            rendered,
        )

        self.assertIn(
            "- Confirmed caller endpoints: 1",
            rendered,
        )

        self.assertIn(
            "- Confirmed callee endpoints: 1",
            rendered,
        )

        self.assertIn(
            "## Confirmed calls by caller",
            rendered,
        )

        self.assertIn(
            (
                "`pkg/app.py::build`\n"
                "  - CALLS "
                "`pkg/worker.py::Worker` "
                "(line 5)"
            ),
            rendered,
        )

        self.assertIn(
            "## Confirmed calls by callee",
            rendered,
        )

        self.assertIn(
            (
                "`pkg/worker.py::Worker`\n"
                "  - CALLED BY "
                "`pkg/app.py::build` "
                "(line 5)"
            ),
            rendered,
        )

        self.assertIn(
            "- Shadowed calls: 1",
            rendered,
        )

        self.assertIn(
            "## Shadowed call candidates",
            rendered,
        )

        self.assertIn(
            "shadowed by `parameter`",
            rendered,
        )

    def test_renderer_shows_confirmed_module_attribute_call(
        self,
    ) -> None:
        index = build_semantic_project_index(
            (
                self.evidence(
                    "pkg/app.py",
                    (
                        "import pkg.worker "
                        "as worker\n"
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
        )

        rendered = render_dependency_graph(
            build_dependency_graph(
                index
            )
        )

        self.assertIn(
            (
                "[CALL] "
                "`pkg/app.py::run` "
                "→ "
                "`pkg/worker.py::module_execute`"
            ),
            rendered,
        )

        self.assertIn(
            (
                "`pkg/worker.py::module_execute`\n"
                "  - CALLED BY "
                "`pkg/app.py::run` "
                "(line 4)"
            ),
            rendered,
        )


    def test_renderer_shows_confirmed_imported_class_attribute_call(
        self,
    ) -> None:
        index = build_semantic_project_index(
            (
                self.evidence(
                    "pkg/app.py",
                    (
                        "from .worker "
                        "import Worker\n"
                        "\n"
                        "def run():\n"
                        "    return "
                        "Worker.execute(None)\n"
                    ),
                ),
                self.evidence(
                    "pkg/worker.py",
                    (
                        "class Worker:\n"
                        "    def execute(self):\n"
                        "        return True\n"
                    ),
                ),
            )
        )

        rendered = render_dependency_graph(
            build_dependency_graph(
                index
            )
        )

        self.assertIn(
            (
                "[CALL] "
                "`pkg/app.py::run` "
                "→ "
                "`pkg/worker.py::Worker.execute`"
            ),
            rendered,
        )

        self.assertIn(
            (
                "`pkg/worker.py::Worker.execute`\n"
                "  - CALLED BY "
                "`pkg/app.py::run` "
                "(line 4)"
            ),
            rendered,
        )


    def test_renderer_shows_confirmed_local_instance_method_call(
        self,
    ) -> None:
        index = build_semantic_project_index(
            (
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
        )

        rendered = render_dependency_graph(
            build_dependency_graph(
                index
            )
        )

        self.assertIn(
            (
                "[CALL] "
                "`pkg/app.py::run` "
                "→ "
                "`pkg/app.py::Worker.execute`"
            ),
            rendered,
        )

        self.assertIn(
            (
                "`pkg/app.py::Worker.execute`\n"
                "  - CALLED BY "
                "`pkg/app.py::run` "
                "(line 7)"
            ),
            rendered,
        )


    def test_renderer_shows_confirmed_direct_class_method_local_instance_call(
        self,
    ) -> None:
        index = build_semantic_project_index(
            (
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
        )

        rendered = render_dependency_graph(
            build_dependency_graph(
                index
            )
        )

        self.assertIn(
            (
                "[CALL] "
                "`pkg/app.py::Manager.run` "
                "→ "
                "`pkg/app.py::Worker.execute`"
            ),
            rendered,
        )

        self.assertIn(
            (
                "`pkg/app.py::Worker.execute`\n"
                "  - CALLED BY "
                "`pkg/app.py::Manager.run` "
                "(line 8)"
            ),
            rendered,
        )

    def test_renderer_labels_dynamic_call_kinds(
        self,
    ) -> None:
        index = build_semantic_project_index(
            (
                self.evidence(
                    "pkg/app.py",
                    (
                        "def run(callback, callbacks):\n"
                        "    callback()\n"
                        "    callbacks[0]()\n"
                    ),
                ),
            )
        )

        rendered = render_dependency_graph(
            build_dependency_graph(
                index
            )
        )

        self.assertIn(
            "- Dynamic calls: 2",
            rendered,
        )

        self.assertIn(
            "kind `callback_parameter`",
            rendered,
        )

        self.assertIn(
            "kind `subscript_selected`",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
