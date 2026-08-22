# Contributing to Project Sniffer

Thank you for considering a contribution to Project Sniffer.

Project Sniffer is currently a pre-1.0, local-first repository-intelligence
tool. The project is being migrated from a small flat Python runtime into an
installable package while preserving the behaviour that already works.

## Core project boundaries

Contributions to the core should preserve these principles:

- scanned projects are treated as read-only;
- target-project source code is not executed;
- target-project dependencies are not installed;
- target databases are not contacted by normal static analysis;
- ordinary analysis does not require network access;
- secret values must not be written to reports, logs, examples, or tests;
- dynamic or unresolved behaviour must not be presented as confirmed fact.

## Current runtime

Project Sniffer now has an installable development package.

The current packaged CLI supports:

```bash
sniff --project /path/to/project --architecture
sniff --project /path/to/project --report
sniff --project /path/to/project --architecture --report
```

Reports are grouped by scanned project:

```text
reports/<project-name>/<files>
```

A custom `--output PATH` changes the base output directory but still keeps the
project-specific subdirectory.

The original root runtime remains temporarily available as a compatibility and
regression reference:

```text
main.py
scanner.py
architecture_builder.py
report_builder.py
utils.py
recommended_ignores.json
```

Do not remove those legacy modules until the packaged scanner/configuration
migration has completed and equivalent behavior remains covered by tests.

## Private and generated material

Do not commit:

```text
docs/private/
reports/
personal_ignores.json
.env
.env.*
virtual environments
build output
local editor state
```

A safe `.env.example` may be committed when it contains no real values.

Synthetic fixtures must not contain private project source code, credentials,
private keys, tokens, cookies, or session material.

## Personal ignore configuration

The installed CLI supports two machine-local `personal_ignores.json` formats
during the 0.x migration period:

```text
legacy global ignore object
schema-version-1 per-project registry
```

The canonical machine-local registry is resolved outside the repository.

The repository-root private file remains only for the temporary legacy
`main.py` compatibility path.

Do not commit either machine-local or repository-root personal configuration.

## Baseline validation

For changes touching the current flat runtime, run at minimum:

```bash
python3 -m compileall \
    -q \
    main.py \
    scanner.py \
    architecture_builder.py \
    report_builder.py \
    utils.py

python3 -m json.tool \
    recommended_ignores.json \
    >/dev/null

python3 -m unittest \
    discover \
    -s tests \
    -p 'test_*.py' \
    -v

git diff --check
```

Changes that affect scanning or report generation should also be exercised
against a synthetic disposable project rather than against private production
repositories.

The packaged architecture and source-report analyzers share one scan manifest.
New analyzer code must consume that shared evidence rather than introducing
another independent project walk.

Target-project `.gitignore` handling also belongs to that shared discovery
layer. Do not implement separate ignore walks inside individual analyzers.

As the package and formal test suite are introduced, this section will be
updated with the canonical package, lint, type-check, and test commands.

## Commit sign-off

Project Sniffer uses Developer Certificate of Origin 1.1 sign-off.

Create signed-off commits with:

```bash
git commit -s
```

The sign-off certifies the contribution under the terms recorded in `DCO`.

## Pull requests

A contribution should explain:

- the problem being solved;
- the implementation approach;
- affected public behaviour;
- tests or verification performed;
- security implications;
- compatibility implications;
- documentation changes.

Keep unrelated refactors out of focused changes where practical.

## Security-sensitive findings

Do not publish real credentials, private keys, tokens, environment values, or
other secret material in examples, issues, patches, tests, or screenshots.

The final public security-reporting channel and community enforcement contact
will be published before Project Sniffer opens for general public
contributions.
