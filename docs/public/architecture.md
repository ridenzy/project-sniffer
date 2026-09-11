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
             +-- project_sniffer.docs_exporter
```

The packaged analyzers currently support `--architecture`, `--report`, and
`--trace`. `--docs` is additionally available as a separate output capability
for copying manifest-approved root-level `docs/public/**` content.

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
- manifest-approved byte-preserving `docs/public/**` export;
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

## Target shared scan pipeline

```text
CLI parsing
    |
Configuration resolution
    |
Project-root validation
    |
Immutable scan settings
    |
Single project walk
    |
Path classification and ignore policy
    |
Canonical ScanManifest
    |
    +-- architecture builder
    |
    +-- safe file reading
    |       |
    |       +-- immutable FileReadResult
    |               |
    |               +-- SourceEvidence
    |                       |
    |                       +-- language classifier
    |                               |
    |                               +-- language registry
    |                                       |
    |                                       +-- parser registry
    |                                               |
    |                                               +-- Python stdlib AST parser
    |                                                       |
    |                                                       +-- SemanticProjectIndex
    |                                                               |
    |                                                               +-- Python import resolution
    |                                                               |
    |                                                               +-- Python call resolution
    |                                                                       |
    |                                                                       +-- DependencyGraph
    |                                                                               |
    |                                                                               +-- CallIndex
    |                                                                               |
    |                                                                               +-- trace renderer
    |                                                                                       |
    |                                                                                       +-- --trace
    +-- --docs raw-byte export
            |
            +-- generated docs/public snapshot
```

Architecture generation, source-report generation, dependency-trace generation,
and `--docs` all consume the same shared scan manifest and do not introduce
separate filesystem discovery walks.

The source-report and trace paths pass discovered files through
`project_sniffer.reading` before Markdown rendering or semantic analysis. The
reader returns immutable `FileReadResult` evidence, rejects paths outside the
resolved project root or inconsistent with the manifest, and does not follow
discovered file symlinks for source content. Binary, oversized, unreadable,
ordinary-symlink, and escaped-symlink outcomes are classified before the report
builder or semantic-analysis pipeline receives source text.

The reader applies an 8 MiB default per-file source-read ceiling and rejects
non-regular filesystem entries before source content is opened.

The documentation-export branch intentionally does not pass files through
`project_sniffer.reading`: `--docs` preserves the original source bytes and
may copy binary documentation. Instead, `project_sniffer.docs_exporter`
filters the existing manifest to root-level `docs/public/**`, validates
source and destination containment, refuses source and destination symlink
hazards, requires regular source files, and performs streamed atomic copies.

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

The current resolver handles direct-name calls conservatively. It can identify
candidate same-file top-level symbols and candidate symbols reached through an
already-resolved internal `from ... import ...` binding, including imported
aliases.

Call resolution currently distinguishes potential internal, unresolved,
ambiguous, and dynamic outcomes. Attribute-chain calls remain unresolved unless
stronger type or binding evidence becomes available, and dynamically computed
call targets remain explicitly dynamic.

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

These outcomes are recorded as `SHADOWED`. This improves false-positive
rejection but still does not promote remaining `POTENTIAL_INTERNAL` candidates
to confirmed call edges.

The resolver now positively confirms a narrow first class of call targets:
direct-name calls backed by one resolved internal `from ... import ...`
binding whose compiler symbol-table entry is imported and has not been
reassigned.

Such outcomes are recorded as `RESOLVED_INTERNAL`. This is static binding proof,
not a guarantee that a call executes at runtime.

`RESOLVED_INTERNAL` calls become `CALL` dependency edges. Same-file top-level
name matches and other weaker candidates remain `POTENTIAL_INTERNAL` until
stronger positive binding proof is implemented.

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
