# Project Sniffer

Project Sniffer is a local-first, read-only repository-intelligence tool for
understanding software projects without executing the target application's
code.

The long-term goal is to provide deterministic repository evidence for
developers, reviewers, and supervised AI-assisted engineering workflows.

## Current development state

Project Sniffer now has an installable development package with the first
working analyzers.

Implemented commands include:

```bash
sniff --project /path/to/project --architecture
sniff --project /path/to/project --report
sniff --project /path/to/project --architecture --report
```

Default output is grouped by scanned project:

```text
reports/<project-name>/
├── <project-name>-architecture.md
└── <project-name>-project-report.md
```

`--output PATH` overrides the base output directory while preserving the
project-specific subdirectory:

```text
PATH/<project-name>/<files>
```

The root-level `main.py` remains available as a positional compatibility entry
point and now delegates to the same packaged runtime used by `sniff`.

## Current capabilities

The existing implementation can:

- recursively scan a project through one shared discovery manifest;
- skip exact-name, basename-glob, and project-relative folder/file rules;
- apply nested target-project `.gitignore` rules deterministically;
- exclude the active Project Sniffer output directory from repeat scans;
- generate a project tree;
- generate a readable Markdown source report;
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

Project Sniffer will distinguish between:

- built-in recommended ignores;
- machine-local per-project preferences;
- project-owned `.project-sniffer.toml` configuration.

The installed CLI now resolves machine-local personal ignores independently of
the invocation directory and supports both the legacy global JSON format and
schema-version-1 per-project profiles.

See:

- `docs/public/architecture.md`
- `docs/public/configuration.md`
- `docs/public/ignore-rules.md`

## Contributing

Project Sniffer is currently in pre-1.0 development.

See `CONTRIBUTING.md` before submitting changes. Contributions use Developer
Certificate of Origin 1.1 sign-off and should be committed with `git commit -s`.

## License

Project Sniffer is licensed under the MIT License. See `LICENSE`.
