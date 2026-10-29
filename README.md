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
sniff --project /path/to/project --report --minus-gitignore
```

`--architecture`, `--report`, and `--trace` are analyzers. `--docs` is a
separate documentation-report capability.

When `--docs` is selected, Project Sniffer inspects the root-level
`docs/public/` and `docs/private/` scopes independently and renders readable
Markdown reports through the existing safe-reader and report-builder
boundaries.

`--minus-gitignore` is a scan control rather than an analyzer. Canonical
analyzer scans apply target-project `.gitignore` rules by default. Supplying
`--minus-gitignore` disables only that target `.gitignore` layer for the
current run; Project Sniffer recommended and personal ignore rules and active
output-directory exclusion remain in force.

`--docs` does not need this override because its explicit documentation-scoped
scans already operate with target-project `.gitignore` processing disabled.

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
