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

`--architecture`, `--report`, and `--trace` are analyzers. `--docs` is an output
capability that copies manifest-approved root-level `docs/public/**`
content alongside generated Project Sniffer evidence.

Default output is grouped by scanned project:

```text
reports/<project-name>/
├── <project-name>-architecture.md
├── <project-name>-project-report.md
├── <project-name>-trace.md
└── docs/
    └── public/
        └── ...
```

The `docs/public/` snapshot is created only when `--docs` is selected and
manifest-approved public documentation exists. Relative paths below
`docs/public/` are preserved.

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
- copy manifest-approved root-level `docs/public/**` files byte-for-byte while
  preserving their relative documentation structure;
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
- parse Python source with the standard-library `ast` module into normalized imports and class, function, and async-function symbol evidence;
- represent unsupported languages, non-text evidence, invalid text evidence, and Python syntax failures through explicit parse statuses;
- build a shared `SemanticProjectIndex` across parsed project sources while
  retaining original parse outcomes and source-file provenance;
- flatten successful parser imports and symbols into reusable project-wide
  evidence without reopening target-project files;
- resolve Python import evidence against scanned project files without importing
  or executing target modules;
- preserve unresolved, ambiguous, and invalid relative imports explicitly rather
  than misclassifying them as confirmed external or internal dependencies;
- recognize the conventional top-level `src/` Python source-root layout during
  internal module resolution;
- build an immutable project dependency graph from confirmed internal Python
  import resolutions;
- preserve every import-resolution outcome while creating dependency edges only
  for relationships supported by deterministic internal evidence;
- retain source path, target path, source line, and enclosing scope on import
  dependency edges;
- render the initial dependency trace from the shared semantic index and
  confirmed internal Python import-resolution evidence;

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

`--docs` is intentionally separate from that analyzer set. It exports
maintained documentation that already survived the shared scan and ignore
policy; it does not perform a second project walk and does not override
recommended, personal, output-directory, or target `.gitignore` exclusions.

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
