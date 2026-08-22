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
             +-- project_sniffer.architecture_builder
             +-- project_sniffer.report_builder
```

The first packaged analyzers now support `--architecture` and `--report`.

The package also contains its recommended ignore configuration as a packaged
resource.

The original root-level runtime remains temporarily available as a regression
reference while the migration continues.

The packaged architecture and source-report analyzers now consume one shared
scan manifest produced by a single deterministic project walk. The legacy
root-level runtime remains separate during the migration period.

## Existing behavior to preserve

The package refactor must preserve:

- directory pruning for ignored folders;
- readable relative paths;
- binary-file skipping;
- unreadable-file tolerance;
- control-character cleaning;
- safe Markdown fencing;
- architecture-tree generation;
- source-report generation;
- clear terminal summaries.

## Known limitations in the current implementation

The current code still has several deliberate migration targets:

1. Ignore matching is currently basename-oriented; project-relative and
   `.gitignore` semantics are not implemented yet.
2. Root-level and packaged scanner/report modules temporarily coexist.
3. The legacy root runtime still has its own repository-local configuration.
4. Legacy DOCX dependencies still remain in `requirements.txt`.
5. No non-overridable secret-bearing source-report exclusions yet.

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

The architecture analyzer must eventually consume the shared scan manifest
instead of performing a second directory walk.

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
