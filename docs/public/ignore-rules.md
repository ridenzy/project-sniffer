# Project Sniffer Ignore Rules

## Current behavior

The packaged shared scanner supports Project Sniffer ignore rules and
target-project `.gitignore` rules.

These are separate policy layers.

## Project Sniffer configuration rules

The existing configuration keys remain:

```text
IGNORE_FOLDERS
IGNORE_FILES
```

Patterns without `/` are basename patterns.

Examples:

```text
node_modules
*.egg-info
agents.json
*.bak
```

These retain the existing case-sensitive basename behavior.

Patterns containing `/` are interpreted as project-relative path patterns.

Examples:

```text
docs/private
frontend/.next
/config/private.json
```

Project-relative patterns always use `/` as their separator, including on
Windows.

Project Sniffer configuration does not use `!` as a re-inclusion operator.
Recommended and personal ignore configuration remains exclusion-oriented.

## Target-project `.gitignore`

Project Sniffer also reads `.gitignore` files found inside the target project.

For example:

```text
.gitignore
src/.gitignore
packages/example/.gitignore
```

Rules are applied relative to the directory containing each `.gitignore`.

A lower-level `.gitignore` can override an applicable rule inherited from a
parent `.gitignore`.

Git-style comments, directory patterns, glob patterns, `**`, and `!` negation
are handled through the packaged `pathspec` dependency.

A `.gitignore` that is itself a symbolic link is not followed.

## Deliberate deterministic boundary

Project Sniffer does not currently read machine-specific Git ignore sources:

```text
.git/info/exclude
core.excludesFile
$XDG_CONFIG_HOME/git/ignore
```

This keeps the same target project from silently producing different scan
manifests merely because it is scanned on another developer's machine.

Only target-tree `.gitignore` files participate in this layer.

## Precedence

Current scanner precedence is:

```text
Project Sniffer recommended/personal rules
    ↓
active Project Sniffer output-directory exclusion
    ↓
target-project .gitignore hierarchy
    ↓
included ScanManifest entry
```

A target `.gitignore` cannot re-include an entry already removed by a Project
Sniffer configuration rule or by output-directory exclusion.

## Excluded parent directories

When a directory is ignored, Project Sniffer prunes it from the single
top-down filesystem walk.

A rule inside that excluded directory therefore cannot re-include one of its
children.

This matches the documented Git behavior for excluded parent directories.

## Shared scan manifest

Architecture and source-report generation continue to consume the same
`ScanManifest`.

`.gitignore` support does not introduce another filesystem discovery walk.

## Generated report directories

Project Sniffer explicitly excludes the resolved project-specific output
directory from the shared scan.

This prevents generated reports from entering later scans when output is
stored inside the target project.

## Personal configuration

The current source-tree development runtime resolves its local private
registry from
`src/project_sniffer/resources/personal_ignores.json`.

The `personal_ignores.json` basename remains excluded by packaged recommended
rules, so the private registry does not enter Project Sniffer's own scan
manifest or source report.

Only schema-version-1 per-project profiles are accepted. The legacy global
personal-ignore shape is rejected.

## Not implemented yet

The current ignore system does not yet implement:

- target-project `.project-sniffer.toml`;
- explicit `--config`;
- Git's machine-local `.git/info/exclude`;
- Git's user-global `core.excludesFile`;
- non-overridable secret-bearing source-report exclusions.

The two Git machine-local sources are intentionally excluded from the current
deterministic scan contract rather than merely forgotten.

## Non-overridable safety exclusions

Normal configuration must eventually be unable to force recognized
secret-bearing material into the complete source report.

Examples include:

- environment files containing values;
- private keys;
- credential stores;
- service-account credentials;
- authentication token stores;
- browser sessions;
- cookie stores;
- other recognized secret-bearing runtime files.

That stronger safety layer remains a prerequisite for the stable `--secret`
analyzer.
