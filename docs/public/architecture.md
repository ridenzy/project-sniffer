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
             +-- project_sniffer.architecture_builder
             +-- project_sniffer.report_builder
             +-- project_sniffer.docs_exporter
```

The packaged analyzers currently support `--architecture` and `--report`.
`--docs` is additionally available as a separate output capability for
copying manifest-approved root-level `docs/public/**` content.

The package also contains its recommended ignore configuration as a packaged
resource.

The current source-tree development runtime may additionally read the local
private schema-version-1 registry at
`src/project_sniffer/resources/personal_ignores.json`. That file is
Git-ignored and excluded from package data.

The root-level `main.py` remains available as a positional compatibility entry
point and delegates to `project_sniffer.application`.

The packaged architecture and source-report analyzers, including the root
compatibility entry point, consume the same configuration, shared scanner,
single scan manifest, safe-reader boundary, architecture builder, and
source-report builder. Obsolete parallel flat runtime implementations have been
removed so `src/project_sniffer/` is the single runtime authority.

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
    |                                       +-- future parser registry
    |                                               |
    |                                               +-- shared project indexes
    |                                                       |
    |                                                       +-- requested analyzers
    |
    +-- --docs raw-byte export
            |
            +-- generated docs/public snapshot
```

Architecture generation, source-report generation, and `--docs` all consume
the same shared scan manifest and do not introduce separate filesystem
discovery walks.

The source-report path passes discovered files through `project_sniffer.reading`
before Markdown rendering. The reader returns immutable `FileReadResult`
evidence, rejects paths outside the resolved project root or inconsistent with
the manifest, and does not follow discovered file symlinks for source content.
Binary, oversized, unreadable, ordinary-symlink, and escaped-symlink outcomes
are classified before `project_sniffer.report_builder` receives any source text.
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
