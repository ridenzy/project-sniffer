# Project Sniffer Ignore Rules

## Current behavior

The present scanner converts `IGNORE_FOLDERS` and `IGNORE_FILES` into Python
sets and performs exact-name membership checks.

This means entries such as:

```text
node_modules
.git
agents.json
```

work when the discovered name matches exactly.

An entry such as:

```text
*.egg-info
```

does not currently behave as a glob pattern.

That limitation is intentional technical debt to be removed by the shared scan
engine.

## Planned ignore engine

The future matcher will support:

- exact folder names;
- exact filenames;
- project-relative paths;
- glob patterns;
- `.gitignore`-style matching;
- controlled negation where safety policy permits it.

## Configuration sources

Ignore rules may eventually come from:

1. built-in defaults;
2. user-wide configuration;
3. target-project `.project-sniffer.toml`;
4. the machine-local per-project personal registry;
5. command-line overrides.

## Non-overridable safety exclusions

Normal configuration must never force recognized secret-bearing material into
the complete source report.

Examples include:

- environment files containing values;
- private keys;
- credential stores;
- service-account credentials;
- authentication token stores;
- browser sessions;
- cookie stores;
- other recognized secret-bearing runtime files.

The secret analyzer may later inspect narrowly controlled metadata from some of
these files, but raw values must not be persisted in ordinary reports.

## Generated report directories

When the selected output directory is inside the scanned project, Project
Sniffer must automatically exclude that output tree from the scan.

This prevents generated reports from recursively appearing inside newer
reports.
