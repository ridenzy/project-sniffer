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
- Maintained public architecture documentation.
- Maintained configuration and ignore-rule documentation.
- Expanded repository-local Git ignore protection.

### Security

- Completed the initial tracked-content publication audit before public
  repository restructuring.
- Confirmed generated reports and private working documentation are not tracked.
