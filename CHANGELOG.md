# Changelog

All notable Project Sniffer changes will be documented in this file.

The project is still in pre-1.0 development.

## Unreleased

### Added

- MIT licensing baseline.
- Developer Certificate of Origin 1.1 contribution policy.
- Initial contributor guidance.
- Initial installable Python package and `sniff` CLI foundation.
- Initial CLI help and version tests.
- Migrated architecture and Markdown source-report execution behind the installed `sniff` command.
- Correct relative project-path resolution for the packaged CLI.
- Project-grouped report directories for default and custom output bases.
- Packaged recommended-ignore resources and a non-creating personal-ignore loader.
- Source-tree-local private personal-ignore registry resolution for the current development runtime.
- Schema-version-1 per-project personal ignore profiles with root-name and root-path matching.
- Shared single-walk scan manifest for the packaged architecture and source-report analyzers.
- Exact and shell-style basename glob matching for current ignore folder and file rules.
- Automatic exclusion of the active project-specific report directory from repeat scans.
- Packaged exclusion for legacy private `personal_ignores.json`.
- Project-relative Project Sniffer ignore patterns.
- Nested target-project `.gitignore` matching with Git-style negation and lower-level overrides.
- Symlink-safe `.gitignore` loading and controlled scan-policy errors.
- Root-level `main.py` compatibility bridge to the packaged analysis runtime.
- Shared safe-file reader producing immutable `FileReadResult` evidence before
  source-report rendering.
- Source-report integration through the shared safe-reader boundary.
- Bounded source reading with an 8 MiB default per-file ceiling and explicit
  oversized-file classification.
- Maintained public architecture documentation.
- Maintained configuration and ignore-rule documentation.
- Expanded repository-local Git ignore protection.
- `--docs` as a separate documentation-report capability for root-level
  `docs/public/` and `docs/private/`, producing canonical public and private
  Markdown reports under the project-specific output directory.
- Scoped documentation discovery that reuses Project Sniffer scanner ignore
  semantics while avoiding a canonical full-project scan for docs-only runs.
- Documentation-scoped safe reading and `SourceEvidence` preparation through
  the shared Markdown report builder rather than raw-byte documentation copies.
- Deliberate disabling of target-project `.gitignore` filtering inside explicit
  documentation scopes while preserving Project Sniffer recommended, personal,
  and active output exclusions.
- Interactive one-run confirmation before overriding a Project Sniffer
  exclusion of `docs/private/`, with all unrelated ignore rules retained.
- Stale private-documentation report cleanup when a later private-scope
  override is declined.
- Shared `SourceEvidence` metadata layered on the existing immutable safe-read
  results without reopening target-project files.
- Deterministic source-language classification for source-report presentation
  and future parser routing.
- Canonical broad language-recognition registry covering general-purpose,
  scripting, web, database, infrastructure, schema, hardware, shader,
  smart-contract, configuration, and documentation source types.
- Maintained `docs/public/language-support.md` capability documentation.
- Initial semantic parser registry and dispatcher for supported source languages.
- Python semantic parsing through the standard-library `ast` module, producing normalized import and class/function symbol evidence without executing target code.
- Shared semantic project indexing that retains all parse outcomes while flattening
  successful import and symbol evidence with source-file provenance.
- Deterministic Python internal-import resolution with explicit resolved,
  unresolved, ambiguous, and invalid-relative-import outcomes.
- Conventional top-level `src/` source-root handling for initial Python module
  resolution without importing or executing target-project modules.
- Immutable dependency-graph evidence derived from confirmed internal Python
  import resolutions while retaining unresolved and ambiguous import evidence.
- Source-file, line, and enclosing-scope provenance on confirmed import
  dependency edges.
- Initial `--trace` CLI analyzer producing a deterministic Markdown dependency
  trace from confirmed internal Python import evidence.
- Shared source-evidence preparation for combined `--report` and `--trace`
  execution so target-project files are not read twice.
- Normalized Python call-site evidence distinguishing direct-name,
  attribute-chain, and dynamic call targets while preserving source line and
  enclosing parser scope.
- Semantic project-index support for flattened call-site evidence without
  reopening target-project source files.
- Conservative Python direct-name call-target candidate resolution against
  same-file top-level symbols and already-resolved internal imported symbols.
- Explicit potential-internal, unresolved, ambiguous, and dynamic Python
  call-resolution outcomes.
- Dependency-trace rendering for Python call candidates while keeping potential
  call targets separate from confirmed dependency edges.
- Compiler-assisted Python call-shadowing detection using existing in-memory
  source evidence without reopening or executing target-project files.
- Explicit shadowed-call outcomes for parameters, assignments, imports,
  nonlocals, closure/free bindings, and other local bindings.
- Positive static proof for stable internal Python `from ... import ...`
  call bindings, producing explicit `RESOLVED_INTERNAL` call outcomes.
- Positive static proof for stable same-file Python direct-name bindings,
  producing `RESOLVED_INTERNAL` outcomes with explicit
  `SAME_FILE_STABLE_BINDING` provenance.
- Conservative AST-based binding checks for same-file definitions, module and
  local import ordering, module-initialization timing, and implicit lambda or
  comprehension shadowing before a call may be positively confirmed.
- Confirmed Python `CALL` dependency edges with caller scope, target symbol,
  source location, and proof provenance.
- Deterministic confirmed-call indexing derived only from existing `CALL`
  dependency edges, providing outbound caller and inbound callee views without
  re-resolving call evidence.
- Dependency-trace caller/callee sections with confirmed caller and callee
  endpoint counts while preserving the original dependency-edge provenance.
- Structured dynamic Python call classification for callback parameters,
  subscript-selected callables, `getattr` results, returned callables, and
  other dynamically computed targets.
- Direct-name calls through runtime parameters with no internal candidate are
  classified as dynamic callback evidence while parameters that shadow a real
  internal candidate remain explicit `SHADOWED` outcomes.
- Dependency-trace dynamic-call entries now include their preserved dynamic
  call kind without promoting uncertain calls into confirmed dependency edges.
- Positive static proof for stable two-part internal Python module-attribute
  calls such as `worker.module_execute()` when the receiver is one resolved
  internal module import and the target is one stable top-level symbol,
  producing explicit `INTERNAL_MODULE_ATTRIBUTE_BINDING` provenance.
- Positive static proof for stable two-part Python class-attribute calls such as
  `Worker.execute(...)` for direct same-file top-level classes and directly
  imported internal classes, producing explicit
  `SAME_FILE_CLASS_ATTRIBUTE_BINDING` and
  `INTERNAL_IMPORTED_CLASS_ATTRIBUTE_BINDING` provenance.
- Conservative attribute-call proof guards for caller-side direct assignment
  and `setattr()` mutation, target rebinding, decorated or rebound methods,
  inheritance, class keywords including metaclasses, and unresolved instance
  receivers so uncertain relationships remain outside confirmed `CALL` edges.

### Removed

- Obsolete root-level scanner, architecture-builder, report-builder, utility,
  and duplicate recommended-ignore implementations after packaged-runtime
  convergence.
- Legacy `requirements.txt` containing unused DOCX-era dependencies; package
  dependencies are defined by `pyproject.toml`.
- Legacy global personal-ignore JSON support and XDG/APPDATA personal-registry resolution.
- Redundant `project_sniffer.scanner` re-export shim after application imports moved directly to `project_sniffer.scanning`.
- Legacy raw-byte `project_sniffer.docs_exporter` implementation and its
  exporter-specific tests after `--docs` moved to scoped Markdown reports.

### Security

- Completed the initial tracked-content publication audit before public
  repository restructuring.
- Confirmed generated reports and private working documentation are not tracked.
- Source reports no longer follow discovered file symlinks and reject escaped,
  outside-project, or manifest/path-mismatch source paths before reading content.
- Oversized source files are skipped without loading their full content, and
  non-regular filesystem entries are refused before source content is opened.
- Documentation reporting rejects symlinked documentation-scope paths and
  unsafe output destinations before report generation, while scoped files use
  the shared safe-reader classification boundary.
- Declining private-documentation exposure removes an existing canonical
  private report so stale sensitive output is not mistaken for current output.