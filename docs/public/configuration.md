# Project Sniffer Configuration

## Current configuration model

The current runtime reads two JSON files:

```text
recommended_ignores.json
personal_ignores.json
```

Both currently use this shape:

```json
{
    "IGNORE_FOLDERS": [],
    "IGNORE_FILES": []
}
```

`main.py` merges the two lists before scanning.

This legacy structure must remain unchanged until the configuration loader is
migrated. Changing `personal_ignores.json` to the future schema before changing
its consumer would silently disable the current personal ignore entries.

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
