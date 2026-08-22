# Project Sniffer Configuration

## Current configuration model

The installed CLI now loads built-in recommended ignores from the packaged
resource:

```text
src/project_sniffer/resources/recommended_ignores.json
```

During the current migration window it may also read an existing legacy:

```text
personal_ignores.json
```

from the invocation working directory.

The packaged loader validates that `IGNORE_FOLDERS` and `IGNORE_FILES` are lists
of strings and never creates or modifies the personal file.

The original root-level `main.py` still uses the older root JSON files and
retains its legacy auto-create behavior.

Removing the remaining working-directory dependency and selecting personal
rules by resolved target project is the next configuration migration stage.

## Planned machine-local per-project registry

The future private `personal_ignores.json` will retain settings for more than
one scanned project.

Planned schema:

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

This file remains:

```text
machine-local
Git-ignored
not distributed with Project Sniffer
```

## Project selection

The future loader will:

1. resolve the requested project root;
2. derive its root name;
3. load the personal registry;
4. select a matching project profile;
5. merge the selected profile with the other configuration sources;
6. construct final scan settings;
7. begin scanning.

A profile may later contain an optional root-path qualifier when multiple local
projects share the same directory name.

Example:

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

Absolute local paths are acceptable inside this private Git-ignored registry,
but they must not be copied into generated public documentation or uploadable
reports.

## Planned project-owned configuration

A target repository may later provide:

```text
.project-sniffer.toml
```

for project-owned scanning rules.

That configuration is separate from the user's private personal registry.

## Planned precedence

Highest priority first:

1. non-overridable Project Sniffer safety rules;
2. command-line overrides;
3. explicit `--config`;
4. matching machine-local personal project profile;
5. target-project `.project-sniffer.toml`;
6. user-wide Project Sniffer configuration;
7. built-in defaults.

The non-overridable safety layer always wins for secret-bearing source-report
exclusions and filesystem escape protection.
