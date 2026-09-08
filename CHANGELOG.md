# Changelog

All notable Project Sniffer changes will be documented in this file.

The project is still in pre-1.0 development.

## Unreleased

### Added

- MIT licensing baseline.
- Developer Certificate of Origin 1.1 contribution policy.
- Initial contributor guidance.
- Initial installable Python package and `sniff` CLI foundation.
- Initial CLI help and version tests.
- Migrated architecture and Markdown source-report execution behind the installed `sniff` command.
- Correct relative project-path resolution for the packaged CLI.
- Project-grouped report directories for default and custom output bases.
- Packaged recommended-ignore resources and a non-creating legacy personal-ignore loader.
- Deterministic machine-local personal-ignore registry resolution.
- Schema-version-1 per-project personal ignore profiles with root-name and root-path matching.
- Backward-compatible support for the legacy global personal-ignore shape during the 0.x migration.
- Shared single-walk scan manifest for the packaged architecture and source-report analyzers.
- Exact and shell-style basename glob matching for current ignore folder and file rules.
- Automatic exclusion of the active project-specific report directory from repeat scans.
- Packaged exclusion for legacy private `personal_ignores.json`.
- Project-relative Project Sniffer ignore patterns.
- Nested target-project `.gitignore` matching with Git-style negation and lower-level overrides.
- Symlink-safe `.gitignore` loading and controlled scan-policy errors.
- Root-level `main.py` compatibility bridge to the packaged analysis runtime.
- Shared safe-file reader producing immutable `FileReadResult` evidence before
  source-report rendering.
- Source-report integration through the shared safe-reader boundary.
- Bounded source reading with an 8 MiB default per-file ceiling and explicit
  oversized-file classification.
- Maintained public architecture documentation.
- Maintained configuration and ignore-rule documentation.
- Expanded repository-local Git ignore protection.

### Removed

- Obsolete root-level scanner, architecture-builder, report-builder, utility,
  and duplicate recommended-ignore implementations after packaged-runtime
  convergence.
- Legacy `requirements.txt` containing unused DOCX-era dependencies; package
  dependencies are defined by `pyproject.toml`.

### Security

- Completed the initial tracked-content publication audit before public
  repository restructuring.
- Confirmed generated reports and private working documentation are not tracked.
- Source reports no longer follow discovered file symlinks and reject escaped,
  outside-project, or manifest/path-mismatch source paths before reading content.
- Oversized source files are skipped without loading their full content, and
  non-regular filesystem entries are refused before source content is opened.
