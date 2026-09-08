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
             +-- project_sniffer.scanner
             +-- project_sniffer.reading
             +-- project_sniffer.architecture_builder
             +-- project_sniffer.report_builder
```

The first packaged analyzers now support `--architecture` and `--report`.

The package also contains its recommended ignore configuration as a packaged
resource.

The root-level `main.py` remains available as a positional compatibility entry
point and delegates to `project_sniffer.application`.

The packaged architecture and source-report analyzers, including the root
compatibility entry point, now consume the same configuration, shared scanner,
single scan manifest, architecture builder, and source-report builder. The
older flat helper modules remain only as migration and regression references.

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
- clear terminal summaries.

## Known limitations in the current implementation

The current code still has several deliberate migration targets:

1. Target-project `.project-sniffer.toml` and explicit `--config` are not
   implemented yet.
2. Older flat scanner/report helper modules temporarily coexist as migration
   references, but the root `main.py` entry point no longer executes them.
3. Legacy DOCX dependencies still remain in `requirements.txt`.
4. Non-overridable secret-bearing exclusions are not implemented yet.

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
Safe file reading
    |
Language parsers and detectors
    |
Shared project indexes
    |
Requested analyzers
    |
Markdown and JSON reporting
```

Architecture and source-report generation now consume the same shared scan
manifest and do not introduce separate filesystem discovery walks.

The source-report path passes discovered files through `project_sniffer.reading`
before Markdown rendering. The reader returns immutable `FileReadResult`
evidence, rejects paths outside the resolved project root or inconsistent with
the manifest, and does not follow discovered file symlinks for source content.
Binary, oversized, unreadable, ordinary-symlink, and escaped-symlink outcomes
are classified before `project_sniffer.report_builder` receives any source text.
The reader applies an 8 MiB default per-file source-read ceiling and rejects
non-regular filesystem entries before source content is opened.

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

Three configuration classes are planned:

1. Built-in defaults and recommended ignores.
2. Machine-local user preferences, including per-project private ignores.
3. Target-project `.project-sniffer.toml` configuration.

The machine-local personal registry is intentionally not committed to Git.

See `configuration.md`.
