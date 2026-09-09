# Project Sniffer Configuration

## Current configuration model

The installed CLI loads recommended ignore rules from the packaged resource
`src/project_sniffer/resources/recommended_ignores.json`.

For the current source-tree development runtime, the local private personal
registry is resolved from
`src/project_sniffer/resources/personal_ignores.json`.

The personal registry is intentionally Git-ignored and excluded from package
data. The loader reads it when present but never creates or modifies it.

The current runtime no longer resolves personal configuration through
`XDG_CONFIG_HOME`, `APPDATA`, or `~/.config`.

This source-tree-local location is a development-stage policy. A final
installed-user personal-configuration location remains to be designed before
1.0.

## Required personal-registry format

Only schema version 1 is accepted.

Example:

    {
        "schema_version": 1,
        "projects": {
            "example-project": {
                "IGNORE_FOLDERS": [
                    "storage",
                    "coverage"
                ],
                "IGNORE_FILES": [
                    "agents.json"
                ]
            }
        }
    }

The old global shape is rejected because personal rules must be scoped to a
project profile.

If an older personal-ignore file still contains rules worth preserving, move
those rules into explicit schema-version-1 project profiles before deleting
the legacy file.

## Project profile selection

Project Sniffer resolves the target project before selecting personal rules.

Matching specificity is:

```text
ROOT_PATH + ROOT_NAME
ROOT_PATH
ROOT_NAME
profile ID matching the project root name
```

The most specific matching profile wins.

Profiles with the same matching specificity are treated as ambiguous and cause
a configuration error rather than being selected arbitrarily.

## Root-name aliases

A profile ID does not have to match the target directory when `ROOT_NAME` is
provided:

```json
{
    "schema_version": 1,
    "projects": {
        "company-a-frontend": {
            "ROOT_NAME": "frontend",
            "IGNORE_FOLDERS": [],
            "IGNORE_FILES": []
        }
    }
}
```

## Root-path qualification

When multiple local repositories share a directory name, `ROOT_PATH` can
identify the intended repository:

```json
{
    "schema_version": 1,
    "projects": {
        "company-a-frontend": {
            "ROOT_NAME": "frontend",
            "ROOT_PATH": "/path/to/company-a/frontend",
            "IGNORE_FOLDERS": [],
            "IGNORE_FILES": []
        }
    }
}
```

Absolute local paths are permitted inside this local private registry.

They must not be copied into generated public examples or uploadable reports.

## Root compatibility entry point

The root-level:

```text
main.py
```

is now a positional compatibility bridge to the packaged application runtime.

Both:

```text
sniff
python3 main.py /path/to/project
```

use packaged recommended ignores, the local private schema-version-1 personal
registry, and the same shared scanner.

The repository-root legacy personal-ignore file and the former XDG/APPDATA
locations are not authoritative for either current entry point.

## Target-project `.gitignore`

The shared scanner reads `.gitignore` files inside the target project.

Nested `.gitignore` files apply relative to their own directory and can
override matching parent `.gitignore` rules.

This discovery layer is intentionally separate from Project Sniffer's own
configuration precedence.

Project Sniffer does not currently consume `.git/info/exclude` or user-global
Git ignore configuration, because those machine-specific sources would make
the same target project produce different scan manifests on different
machines.

Project Sniffer recommended and personal exclusions remain stronger than
target `.gitignore` rules.

## Planned project-owned configuration

A target project may later provide:

```text
.project-sniffer.toml
```

for project-owned scanning rules.

That configuration is separate from local private personal preferences and is
not implemented by the current development runtime.

## Target precedence

The intended complete precedence remains, highest priority first:

1. non-overridable Project Sniffer safety rules;
2. command-line overrides;
3. explicit `--config`;
4. matching local private personal project profile;
5. target-project `.project-sniffer.toml`;
6. user-wide Project Sniffer configuration;
7. built-in defaults.

Only the currently implemented layers participate today.

Non-overridable safety rules will remain authoritative for secret-bearing
source-report exclusions and filesystem escape protection.
