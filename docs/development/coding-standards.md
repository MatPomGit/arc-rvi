# Engineering and Python standards

Read this page before changing Python or its public data contracts.

## Scope and architecture

Keep algorithms in `src/rvi/` independent of the hardware adapter,
sensor brand, image source and deployment method. The CLI in `src/rvi/cli.py`
should validate inputs and invoke existing modules. Shared contracts are
defined in `src/rvi/interfaces.py`. Do not write a new entrypoint or runner
when an existing one can be extended.

Use KISS, DRY, YAGNI, explicit interfaces, dependency inversion only where
needed, and a single source for every configuration value. Preserve versioned
JSON schemas unless a documented migration is required.

## Applicable Python standards

- PEP 8: `snake_case` functions, `CapWords` classes, clear imports,
  meaningful private names and readable formatting.
- PEP 20: simplicity and explicit failure over magic or silent coercion.
- PEP 257: explain non-obvious behavior, not every trivial line.
- PEP 484: type public boundaries and essential domain contracts.
- PEP 3131: the standard library's ASCII naming rules are not a blanket
  restriction on third-party projects. Public source identifiers here
  should remain consistent with current ASCII names.
- PEP 517/518/621: keep the setuptools build and metadata in
  `pyproject.toml`; no duplicate build configuration.
- PEP 660: editable installs through `python -m pip install -e .`.
- PEP 751: consider a generated lockfile only when compatible tooling
  and a reproducibility requirement justify it. Never hand-write one.

Prefer 79-character code lines and concise comments near 72 characters
unless clarity, existing style or automated tooling requires otherwise.
Use UTF-8 and LF. Follow any existing local module style before refactoring.
Do not reformat unrelated code for cosmetic compliance.

## Dependencies and packaging

The current core runtime has no third-party package dependencies.
Prefer the standard library and existing algorithms. Before adding a
dependency, justify functionality, compatibility with Python 3.11+,
license, security, update policy and reproducible installation.

Retain setuptools unless there is a demonstrated packaging limitation.
Do not switch to Hatch or Flit solely for preference. Keep documentation
requirements separately pinned in `docs/requirements-docs.txt`.
Never create duplicate schedulers, queues, GitHub deployment workflows or
speculative shared packages.

## Error handling and testing

Fail explicitly on unknown variants, non-finite measurements,
unsupported URDF geometry, incomplete transforms, invalid units,
unknown friction and inaccessible return routes. Test negative paths,
out-of-range inputs, concurrency/races when applicable and reproducibility.
Do not disable an assertion or replace an error with a fake numeric zero.

For physical systems, software validation never certifies safe motion.
Read `docs/safety.md` before any read-only robot inspection, and require
a separate reviewed physical procedure before any actuation.

## Configuration and hygiene

`pyproject.toml` is the package authority. `PROJECT_STATE.yaml`
is the research-state record and mirrors the version. Configuration
inputs in `config/` describe declared settings, not measured properties.
Use `.gitignore` and the project's text-format conventions. Add
optional tooling (Ruff, codespell, pre-commit or type checkers) only with
a justified scope and deterministic local/CI parity.
