# Project Sniffer Ignore Rules

## Current behavior

The packaged shared scanner now supports both exact basename rules and
shell-style basename glob rules in:

```text
IGNORE_FOLDERS
IGNORE_FILES
```

Examples:

```text
node_modules
.git
agents.json
*.egg-info
*.bak
```

The matcher is case-sensitive and deterministic.

Folder rules are applied only to discovered directory names.

File rules are applied only to discovered filenames.

## Shared scan manifest

The installed architecture and source-report analyzers now consume the same
project scan manifest.

The repository is walked once for their shared discovery phase.

This removes the earlier architecture-specific second `os.walk`.

## Generated report directories

Project Sniffer explicitly excludes the resolved project-specific output
directory from the shared scan.

This allows a custom output base to live inside the scanned project without
causing previously generated reports to recursively enter later reports.

The project root itself cannot be selected as the report directory.

## Personal configuration

The legacy filename:

```text
personal_ignores.json
```

is excluded by the packaged recommended rules.

Machine-local personal configuration belongs outside scanned repositories.

The repository-root copy remains temporarily relevant only to the legacy
root-level `main.py` compatibility path.

## Not implemented yet

The current basename matcher does not yet implement:

- project-relative ignore paths;
- `.gitignore` parsing;
- full `.gitignore` matching semantics;
- negated ignore patterns;
- target-project `.project-sniffer.toml` pattern rules.

Those features belong to the next shared-scanner configuration slice rather
than being approximated incorrectly with basename matching.

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

That stronger safety layer remains a later prerequisite for the `--secret`
analyzer.
