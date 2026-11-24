# Building and publishing this documentation

The dedicated `website/` directory contains publication-specific content and
`public-sources.txt`, the explicit source-to-destination manifest. Canonical
scientific protocols remain in `docs/` and `experiments/`; only individually
listed sources may enter the disposable MkDocs tree.

## Local verification

Python 3.11+ is required for the core package. Documentation builds use
Python 3.12 and exact package versions taken from a successful CI environment
(run 40726274868). Refresh the pinned dependency set deliberately when
updating MkDocs, then validate the strict site build.

```bash
python -m pip install --no-deps -r docs/requirements-docs.txt
python -m pip check
python scripts/validate.py
python scripts/check_agent_docs.py
python scripts/build_docs.py
python -m mkdocs build --strict
python scripts/audit_public_site.py
python -m mkdocs serve
```

The staging source and built site live under ignored `.build/`. Do not edit
generated files. The public homepage, software overview, scientific status
and public evidence guidance live in `website/content/`. The manifest
selects these pages and individually approved canonical scientific documents,
stylesheets and manuscript scaffolds. It never recursively imports repository
directories. The internal documentation audit remains separate from publication.
The staging check rejects internal operational terminology and unsafe paths.
A rejected source must be reviewed and corrected before publishing. The
rendered HTML, search index and text assets undergo an additional boundary
check before upload. These lexical checks complement editorial review;
they are not a proof of confidentiality or a classifier of all operational prose.

## Agent documentation contract and PR gates

`scripts/check_agent_docs.py` is a no-network, standard-library check.
It verifies the two main `AGENTS.md` sections, eight workflow steps,
required safety/testing instructions, local links in canonical repository Markdown
sources, explicit publication-manifest navigation coverage and agreement between
`pyproject.toml` and `PROJECT_STATE.yaml`. Negative regressions live in
`tests/unit/test_agent_docs.py`; workflow release gates are covered by
`tests/unit/test_docs_build.py`. Other documents, external URLs, citations,
runtime correctness and research validity require separate review.

The documentation job runs alongside the Python matrix; publication requires
both jobs to pass and is restricted to `main`.

The existing [GitHub workflow](https://github.com/MatPomGit/arc-rvi/blob/main/.github/workflows/docs-pages.yml)
runs offline regression on Python 3.11, 3.12 and 3.13. After tests,
its `Validate and build documentation` job runs this audit and MkDocs
strict and the rendered publication audit. Require those four check names on the final PR SHA; do not use
an earlier green run. A skipped publishing job on PRs is expected.

GitHub settings are **not** configured by this Markdown or the workflow.
An administrator must verify an active ruleset for `main` under
**Settings > Rules > Rulesets**, with PR integration, the four named
passing checks, restrictions on destructive actions and appropriate bypass
permissions. The owner and reviewer agent share a GitHub account: a genuine,
traceable independent technical review recorded as a PR `COMMENTED` review
or comment meets the project's technical review policy without formal
GitHub `APPROVED`. Each review requires the exact SHA, reviewer role,
inspected scope, evidence, findings and an explicit pass/block conclusion.
A comment is not a GitHub approval and does not satisfy any configured
rule demanding `APPROVED`. Do not change or bypass enforced rules as part
of reviewing or merging. Changes to branch settings are separate
administrative actions; verify them in the GitHub interface. Treat an
unreadable protection API (403) as unknown, not disabled. See [technical
review policy](development/testing.md) and [governance Issue #117](https://github.com/MatPomGit/arc-rvi/issues/117).

## Publishing

The documentation workflow validates pull requests without publishing. A
successful build on `main` uploads a static artifact and deploys it to
GitHub Pages through the restricted `github-pages` environment.

Repository administrators must select **Settings → Pages → Build and deployment
→ GitHub Actions** as the Pages publishing source if it is not already enabled.
No publication is proven until a successful deployment is observed.

The expected project URL is:
https://matpomgit.github.io/arc-rvi/

Only public synthetic examples, open documentation, and text manuscript
scaffolds are staged. Raw data, secrets, run artifacts, and equipment
identifiers must never enter the site. The site is research documentation,
not evidence of completed studies or physical safety certification.

## Published guidance and appearance

The public navigation contains scientific and software documentation only.
Internal development, contribution and automation material is excluded.
Add a public page by reviewing its content and adding its exact source and
destination to `website/public-sources.txt` and the corresponding navigation
entry. Never publish a whole repository directory.

MkDocs 1.6.1 provides native Bootstrap 5 colour schemes. The site uses
`color_mode: auto`, an explicit light/dark/auto menu and a dark high-contrast
navigation bar. The CSS in `docs/assets/theme.css` changes only layout,
reading width and code-block scrolling; it uses native Bootstrap colour
variables rather than overriding light/dark backgrounds globally. The
stylesheet is copied into the MkDocs staging tree by
`scripts/build_docs.py`. The short homepage links to the public software overview; detailed commands remain in canonical scientific documentation.
Validate dark and light appearances at desktop and mobile widths when
browsers are available. A strict build does not measure WCAG contrast,
keyboard usability or actual rendered layout.

Existing sources provide the project's roadmap (`AUTOPILOT_PLAN.md` and
live [Issue #6](https://github.com/MatPomGit/arc-rvi/issues/6)),
software inventory (`pyproject.toml`, `README.md` and architecture),
hardware boundaries (`config/robot.yaml`, architecture and safety) and
research methods (`docs/methodology.md`, `docs/reproducibility.md`).
Do not create separate `docs/roadmap.md`, `docs/software.md`,
`docs/hardware.md` or parallel research protocols without a new,
independent information need. Future experiment dates require an
approved schedule; planned milestones are not verified deadlines.

Source LaTeX manuscripts are not automatically compiled to browser
previews by this pipeline; publication of rendered drafts requires
a separately verified build and rights review.
