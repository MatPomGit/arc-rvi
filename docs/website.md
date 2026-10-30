# Building and publishing this documentation

The canonical files remain in the repository root, `docs/`, and
`experiments/`. MkDocs never maintains duplicate research protocols.

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
python -m mkdocs serve
```

The staging source and built site live under ignored `.build/`. Do not edit
generated files. The root `AGENTS.md` is a repository instruction, not a
published MkDocs page; its local Markdown links are checked against the
repository filesystem. The site homepage comes from the concise root
`index.md`; the complete root `README.md` is staged as
`project-readme.md` and appears separately in the Project navigation.
This distinct name avoids MkDocs treating README as a second homepage.
Experiment pages come from their canonical protocols.
Manuscript `.tex` files are provided as source links, not interpreted as
finished publications.

## Agent documentation contract and PR gates

`scripts/check_agent_docs.py` is a no-network, standard-library check.
It verifies the two main `AGENTS.md` sections, eight workflow steps,
required safety/testing instructions, local links in canonical project
documents and agreement between `pyproject.toml` and
`PROJECT_STATE.yaml`. Tests with intentionally broken examples live in
`tests/unit/test_agent_docs.py`. Other documents, external URLs, citations,
runtime correctness and research validity require separate review.

The existing [GitHub workflow](https://github.com/MatPomGit/arc-rvi/blob/main/.github/workflows/docs-pages.yml)
runs offline regression on Python 3.11, 3.12 and 3.13. After tests,
its `Validate and build documentation` job runs this audit and MkDocs
strict. Require those four check names on the final PR SHA; do not use
an earlier green run. A skipped publishing job on PRs is expected.

GitHub settings are **not** configured by this Markdown or the workflow.
An administrator must set a ruleset for `main` under
**Settings > Rules > Rulesets**, requiring PRs, the four named passing
checks, and at least one approval from a qualified reviewer other than
the change author. Dismiss stale approvals and restrict bypass rights.
For work affecting code, methodology, safety or agent operating rules,
do not merge without an independently recorded approval. Changes to
branch settings are a separate administrative action and must be verified
in the GitHub interface. Treat unreadable branch protection (API 403)
as unknown, not disabled.

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

The public navigation includes agent operating guidance, coding and testing
standards, writing rules, the optional teaching standard and the bilingual
terminology glossary. The root `AGENTS.md` remains a repository instruction;
the website displays linked supporting documents without replacing it.

MkDocs 1.6.1 provides native Bootstrap 5 colour schemes. The site uses
`color_mode: auto`, an explicit light/dark/auto menu and a dark high-contrast
navigation bar. The CSS in `docs/assets/theme.css` changes only layout,
reading width and code-block scrolling; it uses native Bootstrap colour
variables rather than overriding light/dark backgrounds globally. The
stylesheet is copied into the MkDocs staging tree by
`scripts/build_docs.py`. The short homepage avoids placing the complete
CLI reference above the fold; full commands remain in the README.
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
