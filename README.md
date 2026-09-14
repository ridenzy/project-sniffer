# Project Sniffer

Project Sniffer is a local-first, read-only repository-intelligence tool for
understanding software projects without executing the target application's
code.

The long-term goal is to provide deterministic repository evidence for
developers, reviewers, and supervised AI-assisted engineering workflows.

## Current development state

Project Sniffer now has an installable development package with the first
working analyzers.

Implemented operations include:

```bash
sniff --project /path/to/project --architecture
sniff --project /path/to/project --report
sniff --project /path/to/project --trace
sniff --project /path/to/project --docs
sniff --project /path/to/project --architecture --report --trace --docs
```

`--architecture`, `--report`, and `--trace` are analyzers. `--docs` is a
separate documentation-report capability.

When `--docs` is selected, Project Sniffer inspects the root-level
`docs/public/` and `docs/private/` scopes independently and renders readable
Markdown reports through the existing safe-reader and report-builder
boundaries.

Default output is grouped by scanned project:

```text
reports/<project-name>/
├── <project-name>-architecture.md
├── <project-name>-project-report.md
├── <project-name>-trace.md
├── <project-name>-public-docs-report.md
└── <project-name>-private-docs-report.md
```

Only outputs requested and available for the current run are created.

A missing `docs/public/` or `docs/private/` scope produces no report for that
scope.

Documentation-scoped scans continue to apply Project Sniffer recommended and
personal ignore rules, as well as active output-directory exclusion. Target
project `.gitignore` rules are intentionally not applied to these scoped
documentation scans, allowing explicitly requested documentation such as a
Git-ignored `docs/private/` tree to remain inspectable.

If Project Sniffer configuration excludes the `docs/private/` scope, the CLI
warns before exposing it and asks for one-run confirmation. Approval overrides
only that private-scope exclusion for the current run; other Project Sniffer
ignore rules remain active. Declining, submitting an empty response, or having
no interactive response leaves the scope excluded. A stale canonical private
documentation report is removed when that private-scope override is declined.

`--output PATH` overrides the base output directory while preserving the
project-specific subdirectory:

```text
PATH/<project-name>/<files>
```

The root-level `main.py` remains available as a positional compatibility entry
point and delegates to the packaged runtime used by `sniff`. It preserves the
original architecture-plus-report behavior; `--trace` and `--docs` are selected
explicitly through the installed CLI.

## Current capabilities

The existing implementation can:

- recursively scan a project through one shared discovery manifest;
- skip exact-name, basename-glob, and project-relative folder/file rules;
- apply nested target-project `.gitignore` rules deterministically;
- exclude the active Project Sniffer output directory from repeat scans;
- generate a project tree;
- generate a readable Markdown source report;
- generate separate Markdown documentation reports for root-level
  `docs/public/` and `docs/private/` scopes;
- run documentation scopes through the shared safe reader, source-evidence
  metadata, and Markdown report builder rather than raw-byte copying;
- keep Project Sniffer recommended and personal ignore rules active inside
  documentation scopes while deliberately disabling target-project
  `.gitignore` filtering for those scoped scans;
- require explicit one-run approval before overriding a Project Sniffer
  exclusion of `docs/private/`, and remove a stale canonical private report
  when that approval is declined;
- read source-report files through a shared safe-reader evidence boundary;
- refuse to follow discovered file symlinks for source content;
- distinguish escaped symlinks and reject paths outside the resolved project root;
- skip obvious binary files;
- enforce an 8 MiB default per-file source-read ceiling and classify oversized
  files without loading their full content;
- tolerate unreadable files;
- clean unsafe control characters;
- generate Markdown fences that do not collide with source backticks;
- report added and skipped file counts.
- attach deterministic `SourceLanguage` metadata to safe-read source evidence;
- recognize a broad registry of general-purpose, scripting, database,
  infrastructure, web, hardware, shader, smart-contract, configuration, and
  documentation languages from conservative path evidence;
- preserve ambiguous source extensions as `UNKNOWN` rather than guessing;
- route readable source evidence through a semantic parser registry without reopening target-project files;
- parse Python source with the standard-library `ast` module into normalized
  imports, call sites, and class, function, and async-function symbol evidence;
- represent unsupported languages, non-text evidence, invalid text evidence, and Python syntax failures through explicit parse statuses;
- build a shared `SemanticProjectIndex` across parsed project sources while
  retaining original parse outcomes and source-file provenance;
- flatten successful parser imports, symbols, and call sites into reusable
  project-wide evidence without reopening target-project files;
- resolve Python import evidence against scanned project files without importing
  or executing target modules;
- preserve unresolved, ambiguous, and invalid relative imports explicitly rather
  than misclassifying them as confirmed external or internal dependencies;
- recognize the conventional top-level `src/` Python source-root layout during
  internal module resolution;
- build an immutable project dependency graph from confirmed internal Python
  imports and positively proven internal Python calls;
- preserve every import- and call-resolution outcome while creating dependency
  edges only for relationships supported by deterministic internal evidence;
- retain source path, target path, source line, and enclosing scope on confirmed
  dependency edges, plus target-symbol provenance on confirmed call edges;
- render dependency traces from the shared semantic index with confirmed
  internal Python `IMPORT` and `CALL` edges;
- normalize Python call sites into direct-name, attribute-chain, and dynamic
  evidence while preserving source line and enclosing parser scope;
- resolve conservative Python direct-name call candidates against same-file
  top-level symbols and already-resolved internal imported symbols;
- preserve potential-internal, unresolved, ambiguous, and dynamic call outcomes
  rather than presenting uncertain calls as confirmed relationships;
- render call-resolution evidence through `--trace` while keeping potential
  call targets separate from confirmed dependency edges;
- use Python compiler symbol-table evidence to reject call candidates shadowed
  by parameters, assignments, imports, closure bindings, and other local
  bindings;
- render shadowed calls separately from potential internal call candidates.
- positively confirm direct-name calls backed by one unique resolved internal
  `from ... import ...` binding whose compiler symbol-table entry has not been
  reassigned and whose binding order is compatible with the call site;
- positively confirm a conservative class of same-file direct-name calls when
  one unique undecorated top-level function, async-function, or class binding is
  statically stable and available before an immediately evaluated call site;
- use already-read Python AST evidence to reject positive proof when explicit
  rebinding, unsafe binding order, or currently unmodelled lambda/comprehension
  shadowing makes the relationship uncertain;
- retain explicit `INTERNAL_IMPORT_BINDING` and
  `SAME_FILE_STABLE_BINDING` proof provenance on positively confirmed calls;
- distinguish confirmed internal calls from potential, shadowed, ambiguous,
  unresolved, and dynamic call evidence;
- render confirmed caller scope and target-symbol relationships through
  `--trace`.
- derive deterministic caller and callee indexes exclusively from confirmed
  `CALL` dependency edges without reopening source files or rerunning call
  resolution;
- group the same confirmed call edges into outbound `CALLS` and inbound
  `CALLED BY` views while retaining their original source-location and symbol
  provenance;
- render confirmed caller-endpoint and callee-endpoint counts plus navigable
  forward and reverse call relationships through `--trace`.
- classify dynamically computed Python call targets as callback-parameter,
  subscript-selected, `getattr`-result, returned-callable, or other dynamic
  evidence while preserving their uncertain status;
- distinguish runtime callback parameters with no matching internal candidate
  from parameters that actually shadow an internal call candidate;
- render dynamic-call kinds through `--trace` without allowing those uncertain
  relationships into confirmed `CALL` dependency edges or caller/callee
  indexes.

## Language recognition

Current language-recognition coverage is documented in
`docs/public/language-support.md`.

Language recognition is not parser support. Parser capability is tracked
separately from recognition.

Python currently has a semantic parser identified as `python-stdlib-ast`. It
uses Python's standard-library AST without importing or executing target
modules. Other registered languages remain recognition-only until a parser
is implemented for them.

## Project Sniffer 1.0 scope

The stable 1.0 command is planned to support five analyzers:

```text
--architecture
    Project structure, technologies, entry points, and architectural roles.

--report
    Safe readable project-source report.

--trace
    Imports, exports, calls, routes, APIs, file operations, and application flow.

--secret
    Secret-bearing file, configuration, and credential-risk review.

--database
    Static schema, migration, query, ORM, and persistence analysis.
```

`--all` will run all stable static analyzers.

`--docs` is intentionally separate from that analyzer set. It performs scoped
documentation scans only for root-level `docs/public/` and `docs/private/`
rather than requiring the canonical full-project analyzer manifest.

Those scoped scans retain Project Sniffer configuration and output-directory
safety rules but intentionally do not apply target-project `.gitignore`
filtering. A Project Sniffer exclusion of `docs/private/` may be overridden
only through the explicit one-run interactive confirmation described above.

A deterministic `--impact` analyzer is planned after 1.0.

## Safety boundaries

Project Sniffer's core is intended to remain:

- local-first;
- read-only toward the scanned project;
- static-analysis based;
- offline by default;
- non-executing toward target-project code;
- non-connecting toward target databases;
- explicit about uncertainty.

Generated reports may contain proprietary source code, internal configuration,
personal information, or other sensitive material. Review reports before
sharing them.

The safe-reader boundary now includes filesystem containment, file-symlink
refusal, regular-file checks, and an 8 MiB default per-file source-read ceiling.
Recognized secret-bearing files still require stronger non-overridable exclusion
before the stable `--secret` analyzer.

## Configuration direction

The current development runtime distinguishes between:

- built-in recommended ignores;
- one local private schema-version-1 per-project registry;
- target-project `.gitignore` rules.

The local private registry is
`src/project_sniffer/resources/personal_ignores.json`.

It is Git-ignored, excluded from package data, and read-only from Project
Sniffer's perspective. The legacy global JSON shape and the former
XDG/APPDATA personal-registry locations are no longer accepted by the current
runtime.

Target-project `.project-sniffer.toml`, explicit `--config`, and a final
installed-user personal-configuration location remain planned rather than
implemented.

## Contributing

Project Sniffer is currently in pre-1.0 development.

See `CONTRIBUTING.md` before submitting changes. Contributions use Developer
Certificate of Origin 1.1 sign-off and should be committed with `git commit -s`.

## License

Project Sniffer is licensed under the MIT License. See `LICENSE`.
