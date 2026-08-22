# Project Sniffer

Project Sniffer is a local-first, read-only repository-intelligence tool for
understanding software projects without executing the target application's
code.

The long-term goal is to provide deterministic repository evidence for
developers, reviewers, and supervised AI-assisted engineering workflows.

## Current development state

The current runnable baseline is still the original flat Python implementation.

Run it with:

```bash
python3 main.py /full/path/to/project
```

It currently generates:

```text
reports/<project-name>-architecture.md
reports/<project-name>-project-report.md
```

The installable `sniff` command described below is part of the next package and
CLI refactor and is not implemented yet.

## Current capabilities

The existing implementation can:

- recursively scan a project;
- skip configured folders and filenames;
- generate a project tree;
- generate a readable Markdown source report;
- skip obvious binary files;
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

Secret-bearing files will receive stronger non-overridable handling as the
security analyzer and shared scanner are introduced.

## Configuration direction

Project Sniffer will distinguish between:

- built-in recommended ignores;
- machine-local per-project preferences;
- project-owned `.project-sniffer.toml` configuration.

The current `personal_ignores.json` format remains supported until its loader is
migrated safely.

See:

- `docs/public/architecture.md`
- `docs/public/configuration.md`
- `docs/public/ignore-rules.md`

## License

Project Sniffer is licensed under the MIT License. See `LICENSE`.
