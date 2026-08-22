# Project Sniffer Architecture

## Purpose

Project Sniffer is a local-first repository-intelligence CLI designed to
collect deterministic evidence about software projects without executing the
target project.

## Current implementation

The current implementation is intentionally small:

```text
main.py
    |
    +-- scanner.py
    |
    +-- architecture_builder.py
    |
    +-- report_builder.py
    |
    +-- utils.py
```

Configuration currently comes from:

```text
recommended_ignores.json
personal_ignores.json
```

`main.py` currently resolves the configuration before it resolves the target
project and then passes the merged ignore dictionary into the scanner,
architecture builder, and report builder.

The scanner and architecture builder currently walk the target project
independently.

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

1. Positional `sys.argv` parsing.
2. Incorrect handling of relative project paths.
3. Multiple project-directory walks.
4. Exact-name ignore matching rather than real glob matching.
5. Working-directory-dependent configuration loading.
6. Legacy DOCX dependencies still present in `requirements.txt`.
7. No non-overridable secret-bearing source-report exclusions yet.

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
