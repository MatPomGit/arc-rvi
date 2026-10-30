# Validation, GitHub CI and secure integration

Follow this document before creating or merging a PR.

## Local commands

Run from the repository root with Python 3.11 or newer:

```bash
python scripts/validate.py
python scripts/check_agent_docs.py
python scripts/build_docs.py
python -m mkdocs build --strict
```

The first command discovers `unittest` tests under `tests/`. The second
checks the agent workflow, canonical Markdown links and package version
consistency. Install pinned MkDocs packages as described in
[the website guide](../website.md) before its build. MkDocs is not a core
package dependency.

## Required GitHub checks

`.github/workflows/docs-pages.yml` uses hosted Ubuntu runners for offline
Python 3.11, 3.12 and 3.13 tests. The dependent documentation job runs the
agent audit and MkDocs strict. A skipped Pages publishing job on PRs is
expected. Publishing runs after a successful build on `main`.

Store exact PR head SHA and the SHA of each associated check-run; a result
from an older commit is not a pass on the new head. Report `PASS`,
`FAIL`, `BLOCKED` and `NOT_RUN` separately. Review the complete diff
and cover positive, negative, boundary and regression behavior.

## Security and independent review

- Use least privilege in CI and no secrets exposed to untrusted PRs.
- Public PRs must never execute untrusted code on a permanent private runner.
- Do not create paid workloads, disable workflow steps or weaken assertions.
- Confirm explicit safety and provenance gates for any robotics or research
  functionality before accepting software-correctness results.
- The owner and AI agent use one GitHub login. Accept an independent
  technical review posted as `COMMENTED` or a substantive PR comment as
  the repository's review evidence, even without a GitHub `APPROVED` event.
  Require a distinct review role or agent execution trace, exact head SHA,
  inspected scope, technical findings, test evidence, and an explicit
  `REVIEW: PASS` or `REVIEW: CHANGES_REQUIRED` conclusion.
- Mere `COMMENTED` state without a real assessment, an author's unverified
  self-review, a stale SHA, or unresolved blocking findings do not satisfy
  the technical review requirement. Keep `TECHNICAL_REVIEW_PASS` separate
  from `GITHUB_APPROVED`.
- For code, safety, research methodology and agent instructions, require
  the above technical review and verified required CI.
- GitHub rulesets are authoritative: if an active rule actually requires
  `APPROVED`, `COMMENTED` cannot meet it. Do not bypass or report PASS.
  If the rule or evidence is unavailable, mark the relevant gate blocked.
- Current administrative setup is tracked by
  [Issue #117](https://github.com/MatPomGit/arc-rvi/issues/117).
  Configuration in a document does not establish branch protection.

## Deployment receipt

Confirm actual merged SHA on `main`, GitHub Pages deployment conclusion,
deployed revision where available, and an appropriate smoke check.
If the publisher is down or a build fails, log failure and fix/rollback
within the established policy. Never equate merging with deployment.

## Data and research

Fixture-only tests establish software semantics, not physical accuracy.
All initiated study trials must remain traceable, including failed and
unsafe candidates. Read [reproducibility](../reproducibility.md) and
[methodology](../methodology.md) for the relevant experimental gates.
