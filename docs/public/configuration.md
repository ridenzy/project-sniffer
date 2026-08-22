# Project Sniffer Configuration

## Current configuration model

The installed CLI loads recommended ignore rules from the packaged resource:

```text
src/project_sniffer/resources/recommended_ignores.json
```

Machine-local personal ignore rules are resolved independently of the shell
working directory.

On Linux and other XDG-oriented environments, the personal registry is:

```text
${XDG_CONFIG_HOME}/project-sniffer/personal_ignores.json
```

when `XDG_CONFIG_HOME` is defined.

Otherwise the default is:

```text
~/.config/project-sniffer/personal_ignores.json
```

On Windows, `APPDATA` is used when available.

The loader reads the personal registry but never creates or modifies it.

## Legacy global personal-ignore format

During the 0.x migration period the old format remains supported:

```json
{
    "IGNORE_FOLDERS": [],
    "IGNORE_FILES": []
}
```

When this format is stored at the machine-local registry location, its rules
continue to apply globally to scanned projects.

This compatibility exists so existing machine-local rules do not stop working
merely because configuration resolution became deterministic.

## Per-project registry format

The preferred machine-local format is schema version 1:

```json
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
```

The file remains:

```text
machine-local
not distributed with Project Sniffer
not part of a scanned project's source configuration
```

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

Absolute local paths are permitted inside this private machine-local registry.

They must not be copied into generated public examples or uploadable reports.

## Legacy root runtime

The original root-level:

```text
main.py
```

still uses the repository-root legacy JSON configuration.

That path remains temporarily available only as a migration/regression
reference.

The installed `sniff` command no longer selects personal configuration from its
invocation working directory.

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

That configuration is separate from machine-local personal preferences and is
not implemented by the current Phase 1 configuration slice.

## Target precedence

The intended complete precedence remains, highest priority first:

1. non-overridable Project Sniffer safety rules;
2. command-line overrides;
3. explicit `--config`;
4. matching machine-local personal project profile;
5. target-project `.project-sniffer.toml`;
6. user-wide Project Sniffer configuration;
7. built-in defaults.

Only the currently implemented layers participate today.

Non-overridable safety rules will remain authoritative for secret-bearing
source-report exclusions and filesystem escape protection.
