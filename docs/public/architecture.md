# Project Sniffer Architecture

## Purpose

Project Sniffer is a local-first repository-intelligence CLI designed to
collect deterministic evidence about software projects without executing the
target project.

## Current implementation

Project Sniffer now has an installable package entry point:

```text
sniff
 |
 +-- project_sniffer.cli
       |
       +-- project_sniffer.application
             |
             +-- project_sniffer.config
             +-- project_sniffer.scanning
             +-- project_sniffer.reading
             +-- project_sniffer.evidence
             +-- project_sniffer.parsing
             +-- project_sniffer.indexing
             +-- project_sniffer.tracing
             +-- project_sniffer.architecture_builder
             +-- project_sniffer.report_builder
             +-- project_sniffer.docs_reporter
```

The packaged analyzers currently support `--architecture`, `--report`, and
`--trace`. `--docs` is additionally available as a separate documentation
report capability for the root-level `docs/public/` and `docs/private/`
scopes.

The package also contains its recommended ignore configuration as a packaged
resource.

The current source-tree development runtime may additionally read the local
private schema-version-1 registry at
`src/project_sniffer/resources/personal_ignores.json`. That file is
Git-ignored and excluded from package data.

The root-level `main.py` remains available as a positional compatibility entry
point and delegates to `project_sniffer.application`.

The packaged analyzers and root compatibility entry point consume the same
configuration, shared scanner, and single scan manifest. Source-report and trace
analysis also share the safe-reader and `SourceEvidence` path. Obsolete parallel
flat runtime implementations have been removed so `src/project_sniffer/` is the
single runtime authority.

## Existing behavior to preserve

The package refactor must preserve:

- directory pruning for ignored folders;
- readable relative paths;
- binary-file skipping;
- bounded per-file source reading with explicit oversized-file classification;
- unreadable-file tolerance;
- control-character cleaning;
- safe Markdown fencing;
- architecture-tree generation;
- source-report generation;
- scoped Markdown reporting for root-level `docs/public/` and `docs/private/`;
- clear terminal summaries.

## Known limitations in the current implementation

The current code still has several deliberate migration targets:

1. Target-project `.project-sniffer.toml` and explicit `--config` are not
   implemented yet.
2. A final installed-user personal-configuration location is not implemented
   yet; the current private registry is source-tree local.
3. Non-overridable secret-bearing exclusions are not implemented yet.

## Target 1.0 analyzer surface

```text
sniff
 |
 +-- --architecture
 +-- --report
 +-- --trace
 +-- --secret
 +-- --database
```

`--all` will select all stable static analyzers.

## Current analysis and documentation pipelines

The analyzer and documentation paths deliberately share reusable components
without sharing the same discovery scope.

```text
CLI parsing
    |
Configuration resolution
    |
Project-root validation
    |
project_sniffer.application
    |
    +-- analyzer request
    |       |
    |       +-- canonical full-project ScanManifest
    |               |
    |               +-- architecture builder
    |               |
    |               +-- safe file reading
    |                       |
    |                       +-- FileReadResult
    |                               |
    |                               +-- SourceEvidence
    |                                       |
    |                                       +-- source report
    |                                       |
    |                                       +-- semantic parsing
    |                                               |
    |                                               +-- SemanticProjectIndex
    |                                                       |
    |                                                       +-- import resolution
    |                                                       +-- call resolution
    |                                                               |
    |                                                               +-- DependencyGraph
    |                                                                       |
    |                                                                       +-- CallIndex
    |                                                                       +-- trace renderer
    |
    +-- --docs
            |
            +-- project_sniffer.docs_reporter
                    |
                    +-- docs/public/ scoped scan
                    |
                    +-- docs/private/ scoped scan
                            |
                            +-- optional one-run private-scope approval
                    |
                    +-- Project Sniffer ignore rules
                    +-- active output exclusion
                    +-- target .gitignore disabled
                    |
                    +-- safe file reading
                            |
                            +-- SourceEvidence
                                    |
                                    +-- Markdown report builder
                                            |
                                            +-- public docs report
                                            +-- private docs report
```

Architecture generation, source-report generation, and dependency-trace
generation consume the canonical full-project manifest when their analyzers are
selected.

`--docs` does not require that manifest. A docs-only run inspects only the
root-level documentation scopes through separate scoped calls to the shared
scanner.

Those documentation scans preserve project-relative Project Sniffer ignore
semantics by applying the appropriate documentation-path prefix. Active output
directory exclusion also remains in force.

Target-project `.gitignore` processing is deliberately disabled for
documentation-scoped scans. This allows explicit documentation reporting to
see material such as `docs/private/` even when that directory is intentionally
Git-ignored.

Documentation files are not copied byte-for-byte. They pass through
`project_sniffer.reading`, receive deterministic `SourceEvidence`, and are
rendered by the shared Markdown report builder. Binary, oversized, unreadable,
symlink, escaped-path, and other unsafe read outcomes therefore remain
classified rather than copied into a report.

Documentation scope paths themselves may not traverse symlinks, and canonical
report destinations are validated before output is replaced or removed.

When Project Sniffer configuration excludes `docs/private/`, the application
requires explicit one-run confirmation before that private scope exclusion is
overridden. Declining the override leaves the scope excluded and removes an
existing stale canonical private report.

## Source evidence and language recognition

Readable source files retain their existing immutable `FileReadResult` evidence.

`project_sniffer.evidence` adds semantic metadata around that object rather than
duplicating source content or reopening files.

`SourceLanguage` represents language identity only. Recognition does not imply
that a parser exists.

Path-recognition rules are owned by
`project_sniffer.evidence.language_registry`. The registry records deterministic
suffixes, special basenames, broad language categories, and intentionally
unresolved ambiguous cases.

Compound suffixes are evaluated longest-first. Exact case-sensitive suffix
rules are evaluated before case-insensitive rules where the distinction is
meaningful.

See `language-support.md` for the current registry.

## Semantic parsing

`project_sniffer.parsing` normalizes import statements, call sites, and class, function, and async-function symbols.

`project_sniffer.parsing` consumes existing `SourceEvidence`; it does not
perform filesystem discovery or reopen target-project files.

The parser registry currently supports Python through the standard-library
`ast` parser identified as `python-stdlib-ast`. The parser normalizes import
statements, call sites, and class, function, and async-function symbols.

Unsupported languages and non-text or invalid evidence remain explicit parse outcomes.
Syntax errors are recorded as parser evidence rather than causing target code
to execute or the scan pipeline to fail.

## Semantic project indexing

`project_sniffer.indexing` consumes existing `SourceEvidence` through the parser
dispatcher and constructs one immutable `SemanticProjectIndex`.

The index retains every `ParsedSource`, including unsupported-language,
non-text, invalid-text, and syntax-error outcomes. Only successfully parsed
sources contribute flattened IndexedImport, IndexedSymbol, and IndexedCall records.

Those indexed records retain their original parser evidence and source path,
providing project-wide semantic evidence without another filesystem walk,
without reopening source files, and without executing target-project code.

The index is an evidence layer rather than a dependency resolver. Python import
resolution and Python call resolution consume the shared index. The `--trace`
analyzer renders both evidence classes. Confirmed internal imports become
`IMPORT` edges, while positively proven internal calls become `CALL` edges.
Potential, shadowed, ambiguous, unresolved, and dynamic call outcomes remain
explicit evidence rather than inferred relationships.

## Python import resolution

`project_sniffer.tracing` now consumes the shared `SemanticProjectIndex` to
resolve normalized Python import evidence against source files already present
in the project evidence.

Resolution does not import target modules, execute target-project code, inspect
the target interpreter environment, install dependencies, or reopen project
source files.

The initial resolver distinguishes resolved internal imports, unresolved
imports, ambiguous internal candidates, and invalid relative imports. An
unresolved import is intentionally not labelled external because the available
static evidence cannot yet prove whether it represents a standard-library,
third-party, missing, dynamically configured, or otherwise unresolved module.

The current path policy recognizes modules rooted directly in the project and
the conventional top-level `src/` Python source layout. Additional source-root
discovery from packaging metadata remains future work.

Import resolution feeds dependency-graph construction. Confirmed internal
imports become `IMPORT` dependency edges. Python call resolution consumes those
resolved import bindings separately and may create `CALL` edges only when its
own positive static proof succeeds.

## Python call candidate resolution

`project_sniffer.tracing.python_calls` consumes the shared
`SemanticProjectIndex` together with the existing Python import resolutions.

The current resolver handles direct-name calls conservatively and also supports
a narrow two-part attribute-call subset. Direct-name candidates can come from
same-file top-level symbols or already-resolved internal
`from ... import ...` bindings, including imported aliases.

For a two-part `receiver.member()` call, C5I can additionally reason about two
receiver families: a stable resolved internal module import, or an explicit
stable class symbol backed by either a same-file top-level class or a directly
imported internal class.

Call resolution still distinguishes potential internal, unresolved, ambiguous,
shadowed, resolved-internal, and dynamic outcomes. Arbitrary instance receivers
such as `service.execute()` and attribute chains outside the narrow proven
receiver forms remain unresolved unless stronger binding or type evidence
becomes available.

Dynamically computed targets remain explicitly uncertain, but the current
Python evidence model now preserves several syntax- and binding-derived dynamic
kinds: callback parameters, subscript-selected callables, `getattr` results,
returned callables, and other dynamic targets. These classifications describe
why a target is dynamic; they do not prove a concrete runtime callee.

A potential internal call is not a confirmed call dependency. Python permits
parameters, assignments, rebinding, closures, and other scope behaviour that can
shadow an apparently matching symbol. Binding and shadowing analysis is therefore
required before potential call candidates can safely become confirmed call
edges.

The call resolver now also uses Python's compiler-generated symbol-table
information from the already-read source text. It does not reopen source files
or execute target code.

Named function/class scopes can therefore reject candidate targets when the
compiler identifies the called name as a parameter, assignment, local import,
nonlocal, free closure binding, or other local binding.

These outcomes are recorded as `SHADOWED`. Shadowed candidates remain
non-confirmed evidence; other candidates may become confirmed only when one of
the resolver's explicit positive static proofs succeeds.

A direct-name call through a function parameter is treated differently when no
internal candidate exists. In that case the parameter is runtime-provided
callable evidence and is retained as a dynamic `callback_parameter` call. If a
same-file or imported internal candidate exists under that name, the parameter
continues to be recorded as shadowing that candidate instead.

The resolver currently has five narrow positive proof kinds.

The first two cover direct-name calls.

`INTERNAL_IMPORT_BINDING` confirms a direct-name call backed by one resolved
internal `from ... import ...` binding when compiler symbol-table evidence shows
the binding is imported and not reassigned, parameter-bound, nonlocal, or free.
Binding-order checks prevent an import that occurs too late for the relevant
call site from proving the relationship.

`SAME_FILE_STABLE_BINDING` confirms a stable same-file direct-name binding. The
candidate must resolve uniquely to one direct top-level function,
async-function, or class definition whose recognized module binding remains
stable.

C5I adds three attribute-call proofs.

`INTERNAL_MODULE_ATTRIBUTE_BINDING` confirms a two-part call such as
`worker.module_execute()` when `worker` is one stable resolved internal module
import and `module_execute` is one stable top-level target in that module.

`SAME_FILE_CLASS_ATTRIBUTE_BINDING` confirms a two-part
`Class.method(...)` call when the class is one stable direct same-file
top-level class and the requested member is one stable direct undecorated
method.

`INTERNAL_IMPORTED_CLASS_ATTRIBUTE_BINDING` applies the same method proof to a
class reached through one stable direct internal import.

The class-attribute proof deliberately rejects classes with inheritance or
class keywords such as an explicit metaclass. Decorated or rebound methods,
caller-side direct attribute assignment, recognized `setattr()` mutation, and
other unstable binding shapes also prevent positive proof.

The resolver uses the already-read Python AST and compiler symbol tables for
these checks; it does not execute target code or reopen source files.

Successful proofs produce `RESOLVED_INTERNAL`. This is static binding evidence,
not a guarantee that the call executes at runtime.

`RESOLVED_INTERNAL` calls become `CALL` dependency edges. Candidates that do
not satisfy positive proof remain potential, shadowed, ambiguous, unresolved,
or dynamic evidence as appropriate.

## Dependency graph

`project_sniffer.tracing.dependency_graph` converts confirmed internal import
and call resolutions into immutable dependency edges.

Every parsed source path remains represented as a graph node, including files
that have no dependency edges. The graph retains the complete import-resolution
and call-resolution collections so uncertain semantic evidence remains visible
without being converted into confirmed relationships.

Only `RESOLVED_INTERNAL` imports and calls currently become dependency edges:

- resolved imports become `IMPORT` edges;
- positively proven resolved calls become `CALL` edges.

Potential, shadowed, ambiguous, unresolved, and dynamic calls do not become
confirmed edges.

Import edges retain source path, target path, source line, enclosing scope, and
their original `ImportResolution`. Call edges additionally retain the confirmed
target symbol and their original `CallResolution` proof evidence.

The dependency graph remains the authoritative confirmed-relationship layer.
The trace renderer consumes the graph directly for raw dependency rendering and
also derives confirmed caller/callee navigation from its `CALL` edges. Broader
trace relationships remain later stages.

## Confirmed call indexing

`project_sniffer.tracing.call_index` derives deterministic forward and reverse
call views from an existing `DependencyGraph`.

The index does not parse source text, reopen project files, rerun import
resolution, or rerun Python call resolution. It consumes only dependency edges
already present in the graph.

Only edges whose kind is `CALL` participate in the index. Because uncertain
potential, shadowed, ambiguous, unresolved, and dynamic call outcomes do not
become dependency edges, they cannot enter the confirmed caller/callee index.

Each confirmed call edge is grouped in two directions:

- the outbound index groups edges by caller source path and caller scope;
- the inbound index groups the same edges by callee source path and confirmed
  target symbol.

Both views retain the original immutable `DependencyEdge` objects rather than
creating a second relationship-evidence type.

The trace renderer exposes these derived relationships as `CALLS` and
`CALLED BY` sections and reports the number of confirmed caller and callee
endpoints separately from the number of confirmed call edges.

## Core safety model

The 1.0 core must:

- make no target-project modifications;
- execute no target-project code;
- install no target-project dependencies;
- connect to no target database;
- make no network request as part of ordinary static analysis;
- avoid following directory symlinks outside the project root;
- prevent recognized secret-bearing files from entering source reports;
- avoid persisting secret values in analysis indexes or output.

## Configuration ownership

The current and planned configuration classes are:

1. Built-in defaults and recommended ignores.
2. Local private per-project preferences for the current source-tree runtime.
3. Target-project `.project-sniffer.toml` configuration.
4. A future installed-user personal-configuration location.

The current private registry is intentionally not committed to Git or included
as package data.

See `configuration.md`.
