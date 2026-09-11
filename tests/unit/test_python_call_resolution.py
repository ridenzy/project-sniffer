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

    def test_global_declaration_does_not_shadow_module_candidate(
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
                .POTENTIAL_INTERNAL
            ),
        )

        self.assertIsNone(
            resolution.shadowed_by
        )

        self.assertEqual(
            len(
                resolution.candidate_targets
            ),
            1,
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

    def test_module_import_reassignment_prevents_confirmation(
        self,
    ) -> None:
        resolutions = self.resolve(
            self.evidence(
                "pkg/app.py",
                (
                    "from .worker import Worker\n"
                    "Worker = replacement\n"
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

        self.assertIsNone(
            resolution.resolved_target
        )

        self.assertIsNone(
            resolution.proof
        )

if __name__ == "__main__":
    unittest.main()
