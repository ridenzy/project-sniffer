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
from project_sniffer.parsing import (
    DynamicCallKind,
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
    CallResolutionProof,
    CallShadowReason,
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

    def test_stable_same_file_top_level_bindings_are_resolved_internal(
        self,
    ) -> None:
        cases = (
            (
                "function",
                "helper",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
            (
                "async_function",
                "helper",
                (
                    "async def helper():\n"
                    "    return True\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
            (
                "class",
                "Worker",
                (
                    "class Worker:\n"
                    "    pass\n"
                    "\n"
                    "def run():\n"
                    "    return Worker()\n"
                ),
            ),
        )

        for (
            case_name,
            target_name,
            source,
        ) in cases:
            with self.subTest(
                case=case_name
            ):
                resolution = self.resolve(
                    self.evidence(
                        "pkg/app.py",
                        source,
                    ),
                )[0]

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .RESOLVED_INTERNAL
                    ),
                )

                self.assertIsNotNone(
                    resolution.resolved_target
                )

                self.assertEqual(
                    (
                        resolution
                        .resolved_target
                        .source_path
                    ),
                    "pkg/app.py",
                )

                self.assertEqual(
                    (
                        resolution
                        .resolved_target
                        .qualified_name
                    ),
                    target_name,
                )

                self.assertIs(
                    resolution.proof,
                    (
                        CallResolutionProof
                        .SAME_FILE_STABLE_BINDING
                    ),
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )

    def test_unstable_same_file_bindings_remain_potential(
        self,
    ) -> None:
        cases = (
            (
                "module_assignment",
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
            (
                "module_import",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "import external as helper\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
            (
                "star_import",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "from external import *\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
            (
                "decorated_definition",
                (
                    "@decorate\n"
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
            (
                "conditional_definition",
                (
                    "if enabled:\n"
                    "    def helper():\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    return helper()\n"
                ),
            ),
            (
                "lambda_parameter",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "callback = "
                    "lambda helper: helper()\n"
                ),
            ),
            (
                "comprehension_target",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "callbacks = [\n"
                    "    helper()\n"
                    "    for helper in factories\n"
                    "]\n"
                ),
            ),
            (
                "module_call_before_definition",
                (
                    "result = helper()\n"
                    "\n"
                    "def helper():\n"
                    "    return True\n"
                ),
            ),
            (
                "decorator_call_before_definition",
                (
                    "@helper()\n"
                    "def run():\n"
                    "    return True\n"
                    "\n"
                    "def helper():\n"
                    "    return True\n"
                ),
            ),
            (
                "default_call_before_definition",
                (
                    "def run(value=helper()):\n"
                    "    return value\n"
                    "\n"
                    "def helper():\n"
                    "    return True\n"
                ),
            ),
        )

        for case_name, source in cases:
            with self.subTest(
                case=case_name
            ):
                resolution = self.resolve(
                    self.evidence(
                        "pkg/app.py",
                        source,
                    ),
                )[0]

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .POTENTIAL_INTERNAL
                    ),
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )

    def test_unmodeled_implicit_scope_shadow_prevents_import_confirmation(
        self,
    ) -> None:
        cases = (
            (
                "lambda_parameter",
                (
                    "callback = "
                    "lambda Worker: Worker()\n"
                ),
            ),
            (
                "comprehension_target",
                (
                    "instances = [\n"
                    "    Worker()\n"
                    "    for Worker in factories\n"
                    "]\n"
                ),
            ),
        )

        for case_name, body in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker "
                            "import Worker\n"
                            + body
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

                self.assertEqual(
                    len(
                        resolutions
                    ),
                    1,
                )

                resolution = (
                    resolutions[0]
                )

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .POTENTIAL_INTERNAL
                    ),
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )

                self.assertEqual(
                    (
                        resolution
                        .candidate_targets[0]
                        .source_path
                    ),
                    "pkg/worker.py",
                )

    def test_stable_imported_symbol_is_resolved_internal(
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
                .RESOLVED_INTERNAL
            ),
        )

        self.assertIsNotNone(
            resolution.resolved_target
        )

        self.assertEqual(
            (
                resolution
                .resolved_target
                .source_path
            ),
            "pkg/worker.py",
        )

        self.assertEqual(
            (
                resolution
                .resolved_target
                .qualified_name
            ),
            "Worker",
        )

        self.assertIs(
            resolution.proof,
            (
                CallResolutionProof
                .INTERNAL_IMPORT_BINDING
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
                .RESOLVED_INTERNAL
            ),
        )

        self.assertIs(
            resolution.proof,
            (
                CallResolutionProof
                .INTERNAL_IMPORT_BINDING
            ),
        )

        """
        self.assertIs(
            resolution.status,
            (
                CallResolutionStatus
                .POTENTIAL_INTERNAL
            ),
        )
        """

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

    def test_internal_module_attribute_binding_is_resolved_internal(
        self,
    ) -> None:
        resolution = self.resolve(
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
        )[0]

        self.assertIs(
            resolution.status,
            (
                CallResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertIsNotNone(
            resolution.resolved_target
        )

        self.assertEqual(
            (
                resolution
                .resolved_target
                .source_path
            ),
            "pkg/worker.py",
        )

        self.assertEqual(
            (
                resolution
                .resolved_target
                .qualified_name
            ),
            "module_execute",
        )

        self.assertIs(
            resolution.proof,
            (
                CallResolutionProof
                .INTERNAL_MODULE_ATTRIBUTE_BINDING
            ),
        )

        self.assertEqual(
            len(
                resolution
                .candidate_targets
            ),
            1,
        )

    def test_unstable_module_attribute_bindings_remain_potential(
        self,
    ) -> None:
        cases = (
            (
                "receiver_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "import pkg.worker "
                            "as worker\n"
                            "worker = replacement\n"
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
                ),
            ),
            (
                "target_reassigned",
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
                            "\n"
                            "module_execute = "
                            "replacement\n"
                        ),
                    ),
                ),
            ),
            (
                "local_import_after_call",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "def run():\n"
                            "    value = "
                            "worker.module_execute()\n"
                            "    import pkg.worker "
                            "as worker\n"
                            "    return value\n"
                        ),
                    ),
                    self.evidence(
                        "pkg/worker.py",
                        (
                            "def module_execute():\n"
                            "    return True\n"
                        ),
                    ),
                ),
            ),
            (
                "caller_attribute_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "import pkg.worker "
                            "as worker\n"
                            "worker.module_execute = "
                            "replacement\n"
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
                ),
            ),
            (
                "caller_setattr_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "import pkg.worker "
                            "as worker\n"
                            "setattr(\n"
                            "    worker,\n"
                            "    \"module_execute\",\n"
                            "    replacement,\n"
                            ")\n"
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
                ),
            )
        )

        for case_name, evidence in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    *evidence
                )

                resolution = next(
                    item
                    for item in resolutions
                    if (
                        len(
                            item
                            .evidence
                            .target_parts
                        ) == 2
                        and (
                            item
                            .evidence
                            .target_parts[-1]
                            == "module_execute"
                        )
                    )
                )

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .POTENTIAL_INTERNAL
                    ),
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )

    def test_module_attribute_implicit_scopes_remain_unresolved(
        self,
    ) -> None:
        cases = (
            (
                "lambda_parameter",
                (
                    "import pkg.worker as worker\n"
                    "\n"
                    "callback = lambda worker: "
                    "worker.module_execute()\n"
                ),
            ),
            (
                "comprehension_target",
                (
                    "import pkg.worker as worker\n"
                    "\n"
                    "values = [\n"
                    "    worker.module_execute()\n"
                    "    for worker in workers\n"
                    "]\n"
                ),
            ),
        )

        for case_name, source in cases:
            with self.subTest(
                case=case_name
            ):
                resolution = self.resolve(
                    self.evidence(
                        "pkg/app.py",
                        source,
                    ),
                    self.evidence(
                        "pkg/worker.py",
                        (
                            "def module_execute():\n"
                            "    return True\n"
                        ),
                    ),
                )[0]

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .UNRESOLVED
                    ),
                )

                self.assertEqual(
                    resolution.candidate_targets,
                    (),
                )


    def test_stable_class_attribute_bindings_are_resolved_internal(
        self,
    ) -> None:
        cases = (
            (
                "same_file_method",
                "pkg/app.py",
                "Worker.execute",
                (
                    CallResolutionProof
                    .SAME_FILE_CLASS_ATTRIBUTE_BINDING
                ),
                (
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
                ),
            ),
            (
                "same_file_async_method",
                "pkg/app.py",
                "Worker.execute",
                (
                    CallResolutionProof
                    .SAME_FILE_CLASS_ATTRIBUTE_BINDING
                ),
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Worker:\n"
                            "    async def execute(self):\n"
                            "        return True\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute(None)\n"
                        ),
                    ),
                ),
            ),
            (
                "imported_class",
                "pkg/worker.py",
                "Worker.execute",
                (
                    CallResolutionProof
                    .INTERNAL_IMPORTED_CLASS_ATTRIBUTE_BINDING
                ),
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
                ),
            ),
            (
                "imported_class_alias",
                "pkg/worker.py",
                "Worker.execute",
                (
                    CallResolutionProof
                    .INTERNAL_IMPORTED_CLASS_ATTRIBUTE_BINDING
                ),
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker "
                            "import Worker as W\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "W.execute(None)\n"
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
                ),
            ),
        )

        for (
            case_name,
            target_path,
            target_name,
            expected_proof,
            evidence,
        ) in cases:
            with self.subTest(
                case=case_name
            ):
                resolution = self.resolve(
                    *evidence
                )[0]

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .RESOLVED_INTERNAL
                    ),
                )

                self.assertIsNotNone(
                    resolution.resolved_target
                )

                self.assertEqual(
                    (
                        resolution
                        .resolved_target
                        .source_path
                    ),
                    target_path,
                )

                self.assertEqual(
                    (
                        resolution
                        .resolved_target
                        .qualified_name
                    ),
                    target_name,
                )

                self.assertIs(
                    resolution.proof,
                    expected_proof,
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )


    def test_unstable_class_attribute_bindings_remain_potential(
        self,
    ) -> None:
        cases = (
            (
                "decorated_method",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Worker:\n"
                            "    @staticmethod\n"
                            "    def execute():\n"
                            "        return True\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute()\n"
                        ),
                    ),
                ),
            ),
            (
                "class_member_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Worker:\n"
                            "    def execute(self):\n"
                            "        return True\n"
                            "    execute = "
                            "replacement\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute(None)\n"
                        ),
                    ),
                ),
            ),
            (
                "module_attribute_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Worker:\n"
                            "    def execute(self):\n"
                            "        return True\n"
                            "\n"
                            "Worker.execute = "
                            "replacement\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute(None)\n"
                        ),
                    ),
                ),
            ),
            (
                "setattr_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Worker:\n"
                            "    def execute(self):\n"
                            "        return True\n"
                            "\n"
                            "setattr(\n"
                            "    Worker,\n"
                            "    \"execute\",\n"
                            "    replacement,\n"
                            ")\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute(None)\n"
                        ),
                    ),
                ),
            ),
            (
                "call_before_class_definition",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "value = "
                            "Worker.execute(None)\n"
                            "\n"
                            "class Worker:\n"
                            "    def execute(self):\n"
                            "        return True\n"
                        ),
                    ),
                ),
            ),
            (
                "imported_target_class_rebound",
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
                            "\n"
                            "Worker = replacement\n"
                        ),
                    ),
                ),
            ),
            (
                "imported_caller_attribute_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker "
                            "import Worker\n"
                            "Worker.execute = "
                            "replacement\n"
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
                ),
            ),
            (
                "imported_alias_setattr_reassigned",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker "
                            "import Worker as W\n"
                            "setattr(\n"
                            "    W,\n"
                            "    \"execute\",\n"
                            "    replacement,\n"
                            ")\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "W.execute(None)\n"
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
                ),
            ),
            (
                "inherited_class",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Base:\n"
                            "    pass\n"
                            "\n"
                            "class Worker(Base):\n"
                            "    def execute(self):\n"
                            "        return True\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute(None)\n"
                        ),
                    ),
                ),
            ),
            (
                "explicit_metaclass",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "class Meta(type):\n"
                            "    def __getattribute__(\n"
                            "        cls,\n"
                            "        name,\n"
                            "    ):\n"
                            "        return replacement\n"
                            "\n"
                            "class Worker(\n"
                            "    metaclass=Meta\n"
                            "):\n"
                            "    def execute(self):\n"
                            "        return True\n"
                            "\n"
                            "def run():\n"
                            "    return "
                            "Worker.execute(None)\n"
                        ),
                    ),
                ),
            ),
        )

        for case_name, evidence in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    *evidence
                )

                resolution = next(
                    item
                    for item in resolutions
                    if (
                        len(
                            item
                            .evidence
                            .target_parts
                        ) == 2
                        and (
                            item
                            .evidence
                            .target_parts[-1]
                            == "execute"
                        )
                    )
                )

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .POTENTIAL_INTERNAL
                    ),
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )


    def test_class_receiver_shadowing_is_not_confirmed(
        self,
    ) -> None:
        resolution = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run(Worker):\n"
                    "    return "
                    "Worker.execute(None)\n"
                ),
            ),
        )[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.SHADOWED,
        )

        self.assertIs(
            resolution.shadowed_by,
            CallShadowReason.PARAMETER,
        )

        self.assertEqual(
            resolution.candidate_targets,
            (),
        )


    def test_local_constructor_instance_calls_are_resolved_internal(
        self,
    ) -> None:
        cases = (
            (
                "same_file_class",
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
                ),
                "pkg/app.py",
            ),
            (
                "imported_class",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker import Worker\n"
                            "\n"
                            "def run():\n"
                            "    worker = Worker()\n"
                            "    return worker.execute()\n"
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
                ),
                "pkg/worker.py",
            ),
            (
                "imported_alias",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker import Worker as W\n"
                            "\n"
                            "def run():\n"
                            "    worker = W()\n"
                            "    return worker.execute()\n"
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
                ),
                "pkg/worker.py",
            ),
        )

        for (
            case_name,
            evidence,
            expected_path,
        ) in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    *evidence
                )

                resolution = next(
                    item
                    for item in resolutions
                    if (
                        item.evidence.target_parts
                        == (
                            "worker",
                            "execute",
                        )
                    )
                )

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .RESOLVED_INTERNAL
                    ),
                )

                self.assertIsNotNone(
                    resolution.resolved_target
                )

                self.assertEqual(
                    resolution.resolved_target.source_path,
                    expected_path,
                )

                self.assertEqual(
                    resolution.resolved_target.qualified_name,
                    "Worker.execute",
                )

                self.assertIs(
                    resolution.proof,
                    (
                        CallResolutionProof
                        .LOCAL_INSTANCE_CONSTRUCTOR_BINDING
                    ),
                )

                self.assertEqual(
                    resolution.candidate_targets,
                    (
                        resolution.resolved_target,
                    ),
                )


    def test_local_constructor_instance_calls_are_resolved_inside_direct_class_methods(
        self,
    ) -> None:
        cases = (
            (
                "same_file_class",
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
                ),
                "pkg/app.py",
            ),
            (
                "imported_class",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker import Worker\n"
                            "\n"
                            "class Manager:\n"
                            "    def run(self):\n"
                            "        worker = Worker()\n"
                            "        return worker.execute()\n"
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
                ),
                "pkg/worker.py",
            ),
            (
                "imported_alias",
                (
                    self.evidence(
                        "pkg/app.py",
                        (
                            "from .worker import Worker as W\n"
                            "\n"
                            "class Manager:\n"
                            "    def run(self):\n"
                            "        worker = W()\n"
                            "        return worker.execute()\n"
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
                ),
                "pkg/worker.py",
            ),
        )

        for (
            case_name,
            evidence,
            expected_path,
        ) in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    *evidence
                )

                resolution = next(
                    item
                    for item in resolutions
                    if (
                        item.evidence.target_parts
                        == (
                            "worker",
                            "execute",
                        )
                    )
                )

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .RESOLVED_INTERNAL
                    ),
                )

                self.assertEqual(
                    resolution.evidence.scope,
                    "Manager.run",
                )

                self.assertIsNotNone(
                    resolution.resolved_target
                )

                self.assertEqual(
                    resolution.resolved_target.source_path,
                    expected_path,
                )

                self.assertEqual(
                    resolution.resolved_target.qualified_name,
                    "Worker.execute",
                )

                self.assertIs(
                    resolution.proof,
                    (
                        CallResolutionProof
                        .LOCAL_INSTANCE_CONSTRUCTOR_BINDING
                    ),
                )


    def test_unproven_dotted_instance_shapes_remain_unresolved(
        self,
    ) -> None:
        cases = (
            (
                "self_receiver",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "    def run(self):\n"
                    "        return self.execute()\n"
                ),
                (
                    "self",
                    "execute",
                ),
                "Worker.run",
            ),
            (
                "nested_function",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "class Manager:\n"
                    "    def run(self):\n"
                    "        def inner():\n"
                    "            worker = Worker()\n"
                    "            return worker.execute()\n"
                    "        return inner()\n"
                ),
                (
                    "worker",
                    "execute",
                ),
                "Manager.run.inner",
            ),
        )

        for (
            case_name,
            source,
            target_parts,
            expected_scope,
        ) in cases:
            with self.subTest(
                case=case_name
            ):
                resolution = next(
                    item
                    for item in self.resolve(
                        self.evidence(
                            "pkg/app.py",
                            source,
                        ),
                    )
                    if (
                        item.evidence.target_parts
                        == target_parts
                    )
                )

                self.assertEqual(
                    resolution.evidence.scope,
                    expected_scope,
                )

                self.assertIs(
                    resolution.status,
                    CallResolutionStatus.UNRESOLVED,
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

    def test_unsafe_local_instance_shapes_remain_unresolved(
        self,
    ) -> None:
        cases = (
            (
                "factory_result",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def factory():\n"
                    "    return Worker()\n"
                    "\n"
                    "def run():\n"
                    "    worker = factory()\n"
                    "    return worker.execute()\n"
                ),
            ),
            (
                "intervening_statement",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    worker = Worker()\n"
                    "    other()\n"
                    "    return worker.execute()\n"
                ),
            ),
            (
                "receiver_parameter",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run(worker):\n"
                    "    worker = Worker()\n"
                    "    return worker.execute()\n"
                ),
            ),
            (
                "custom_init",
                (
                    "class Worker:\n"
                    "    def __init__(self):\n"
                    "        pass\n"
                    "\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    worker = Worker()\n"
                    "    return worker.execute()\n"
                ),
            ),
            (
                "custom_getattribute",
                (
                    "class Worker:\n"
                    "    def __getattribute__(self, name):\n"
                    "        return replacement\n"
                    "\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    worker = Worker()\n"
                    "    return worker.execute()\n"
                ),
            ),
            (
                "inherited_class",
                (
                    "class Base:\n"
                    "    pass\n"
                    "\n"
                    "class Worker(Base):\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    worker = Worker()\n"
                    "    return worker.execute()\n"
                ),
            ),
            (
                "nested_expression",
                (
                    "class Worker:\n"
                    "    def execute(self):\n"
                    "        return True\n"
                    "\n"
                    "def run():\n"
                    "    worker = Worker()\n"
                    "    return other() or worker.execute()\n"
                ),
            ),
        )

        for case_name, source in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    self.evidence(
                        "pkg/app.py",
                        source,
                    ),
                )

                resolution = next(
                    item
                    for item in resolutions
                    if (
                        item.evidence.target_parts
                        == (
                            "worker",
                            "execute",
                        )
                    )
                )

                self.assertIs(
                    resolution.status,
                    CallResolutionStatus.UNRESOLVED,
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

                self.assertEqual(
                    resolution.candidate_targets,
                    (),
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

        self.assertIs(
            resolutions[0].dynamic_kind,
            DynamicCallKind.SUBSCRIPT_SELECTED,
        )

    def test_callback_parameter_without_internal_candidate_is_dynamic(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def run(callback):\n"
                    "    return callback()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.DYNAMIC,
        )

        self.assertIs(
            resolution.dynamic_kind,
            DynamicCallKind.CALLBACK_PARAMETER,
        )

        self.assertIsNone(
            resolution.shadowed_by
        )

        self.assertEqual(
            resolution.candidate_targets,
            (),
        )


    def test_getattr_result_dynamic_kind_is_preserved(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def run(service, name):\n"
                    "    return getattr(service, name)()\n"
                ),
            ),
        )

        self.assertIs(
            resolutions[0].status,
            CallResolutionStatus.DYNAMIC,
        )

        self.assertIs(
            resolutions[0].dynamic_kind,
            DynamicCallKind.GETATTR_RESULT,
        )


    def test_returned_callable_dynamic_kind_is_preserved(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def run():\n"
                    "    return make_callback()()\n"
                ),
            ),
        )

        self.assertIs(
            resolutions[0].status,
            CallResolutionStatus.DYNAMIC,
        )

        self.assertIs(
            resolutions[0].dynamic_kind,
            DynamicCallKind.RETURNED_CALLABLE,
        )

    def test_parameter_shadows_top_level_candidate(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "def run(helper):\n"
                    "    return helper()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.SHADOWED,
        )

        self.assertIs(
            resolution.shadowed_by,
            CallShadowReason.PARAMETER,
        )

        self.assertEqual(
            resolution.candidate_targets,
            (),
        )

    def test_assignment_shadows_imported_candidate(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker import Worker\n"
                    "\n"
                    "def run():\n"
                    "    Worker = None\n"
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
            CallResolutionStatus.SHADOWED,
        )

        self.assertIs(
            resolution.shadowed_by,
            CallShadowReason.ASSIGNMENT,
        )

        self.assertEqual(
            resolution.candidate_targets,
            (),
        )

    def test_local_import_shadows_top_level_candidate(
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
                    "    import external as helper\n"
                    "    return helper()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.SHADOWED,
        )

        self.assertIs(
            resolution.shadowed_by,
            CallShadowReason.IMPORT,
        )

    def test_free_closure_binding_shadows_module_candidate(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "def outer():\n"
                    "    helper = None\n"
                    "\n"
                    "    def inner():\n"
                    "        return helper()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.SHADOWED,
        )

        self.assertIs(
            resolution.shadowed_by,
            CallShadowReason.FREE,
        )

    def test_nonlocal_binding_shadows_module_candidate(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def helper():\n"
                    "    return True\n"
                    "\n"
                    "def outer():\n"
                    "    helper = None\n"
                    "\n"
                    "    def inner():\n"
                    "        nonlocal helper\n"
                    "        return helper()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            CallResolutionStatus.SHADOWED,
        )

        self.assertIs(
            resolution.shadowed_by,
            CallShadowReason.NONLOCAL,
        )

    def test_global_declaration_preserves_stable_module_binding(
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
                    "    global helper\n"
                    "    return helper()\n"
                ),
            ),
        )

        resolution = resolutions[0]

        self.assertIs(
            resolution.status,
            (
                CallResolutionStatus
                .RESOLVED_INTERNAL
            ),
        )

        self.assertIsNone(
            resolution.shadowed_by
        )

        self.assertIsNotNone(
            resolution.resolved_target
        )

        self.assertIs(
            resolution.proof,
            (
                CallResolutionProof
                .SAME_FILE_STABLE_BINDING
            ),
        )

    def test_local_internal_import_is_resolved_internal(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "def run():\n"
                    "    from .worker import Worker\n"
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
                .RESOLVED_INTERNAL
            ),
        )

        self.assertIsNotNone(
            resolution.resolved_target
        )

        self.assertEqual(
            (
                resolution
                .resolved_target
                .source_path
            ),
            "pkg/worker.py",
        )

        self.assertIs(
            resolution.proof,
            (
                CallResolutionProof
                .INTERNAL_IMPORT_BINDING
            ),
        )


    def test_unstable_internal_import_bindings_remain_potential(
        self,
    ) -> None:
        cases = (
            (
                "reassigned_module_binding",
                (
                    "from .worker import Worker\n"
                    "Worker = replacement\n"
                    "\n"
                    "def run():\n"
                    "    return Worker()\n"
                ),
            ),
            (
                "module_call_before_import",
                (
                    "instance = Worker()\n"
                    "from .worker import Worker\n"
                ),
            ),
            (
                "local_call_before_import",
                (
                    "def run():\n"
                    "    instance = Worker()\n"
                    "    from .worker import Worker\n"
                    "    return instance\n"
                ),
            ),
            (
                "decorator_call_before_import",
                (
                    "@Worker()\n"
                    "def run():\n"
                    "    return True\n"
                    "\n"
                    "from .worker import Worker\n"
                ),
            ),
            (
                "default_call_before_import",
                (
                    "def run(value=Worker()):\n"
                    "    return value\n"
                    "\n"
                    "from .worker import Worker\n"
                ),
            ),
        )

        for case_name, source in cases:
            with self.subTest(
                case=case_name
            ):
                resolutions = self.resolve(
                    self.evidence(
                        "pkg/app.py",
                        source,
                    ),
                    self.evidence(
                        "pkg/worker.py",
                        (
                            "class Worker:\n"
                            "    pass\n"
                        ),
                    ),
                )

                self.assertEqual(
                    len(
                        resolutions
                    ),
                    1,
                )

                resolution = (
                    resolutions[0]
                )

                self.assertIs(
                    resolution.status,
                    (
                        CallResolutionStatus
                        .POTENTIAL_INTERNAL
                    ),
                )

                self.assertIsNone(
                    resolution.resolved_target
                )

                self.assertIsNone(
                    resolution.proof
                )

                self.assertEqual(
                    len(
                        resolution
                        .candidate_targets
                    ),
                    1,
                )

if __name__ == "__main__":
    unittest.main()
