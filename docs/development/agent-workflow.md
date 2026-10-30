# Autonomous agent workflow

This page expands the repository root `AGENTS.md`. The root file is normative;
this page gives the operational sequence. Confirm current GitHub state before acting.

## Start and ownership

1. Read the root `AGENTS.md` and any applicable local rules.
2. Confirm the user task, available tools, scope, budget and access.
3. Inspect `main`, worktree, Issues, existing PRs, checks, assignments and dependencies.
4. Before choosing new work, check for merged changes that are not deployed.
5. Prefer completing a compatible existing PR over opening a competing branch.
6. Reserve the task in its Issue with scope, owner/agent and expected acceptance gate.
7. Use an existing lease mechanism when available; never create a second scheduler.
8. Maximum six active work branches and six open PRs for agent-managed work.
9. Limits do not authorize deletion of other agents' work; close and clean safely.
10. Select among ready issues by safety, failure, unfinished PR, deployment debt,
    dependencies, research schedule, features, testing and documentation.

## Ready, doing, done

Definition of Ready (DoR): the objective, acceptance criteria, essential
dependencies, relevant interface contracts and operational permissions are
understood. Missing noncritical details can be researched without escalation.

In progress: preserve a single bounded scope. Update the Issue at meaningful
milestones; avoid excessive status comments and duplicate documents.

Definition of Done (DoD): acceptance demonstrated, changed tests and documents
verified, exact SHA recorded, required review accepted, changes merged and
deployment independently verified if applicable. Issues and temporary leases
must reflect the final state; abandoned work cannot be called complete.

## Integration and deployment

- Use PRs with purpose, scope, linked Issue, risk, tests, remaining gaps and
  precise final SHA. Recheck check-runs after the final commit or rebase.
- Require a separate substantive technical review for source, safety,
  scientific or agent-policy changes. The reviewer may be a distinct AI agent
  using the author's GitHub account. A documented PR `COMMENTED` review or
  discussion comment can satisfy the project's technical-review requirement,
  even without a formal GitHub `APPROVED` event, provided it covers the exact
  head SHA, scope, findings, test evidence and a clear pass/block verdict.
  Verify independent execution or role provenance; the same account alone
  cannot prove that author and reviewer are separate. Ordinary comments,
  self-attestation, stale reviews or unresolved blocking findings do not pass.
  This project decision does not satisfy a mandatory GitHub approval rule.
- If branch rules cannot be read, record UNKNOWN; do not infer they are absent.
- Do not use administrator bypass, weaker CI or changed tests as a shortcut.
- If a pull request is merged by another actor, verify what was actually merged,
  then complete any pending deployment checks and documentation separately.
- This repository publishes MkDocs through `.github/workflows/docs-pages.yml`.
  GitHub Pages success and site availability are separate observations.
- Stop or escalate before physical robot control or unauthorized infrastructure work.
- After successful merge, check that no work remains on your branch, then remove
  your branch/worktree; never delete another agent's unmerged changes.
- Record bounded partial progress and `BLOCKED` when a gate cannot be satisfied.

## Shared-account review record

For each code or methodology PR, check the latest PR review and discussion
comments rather than searching only for GitHub `APPROVED`. A qualifying
review must identify the distinct reviewer role or independently executed
agent and the reviewed commit SHA, state the technical conclusion, document
tests and any blocking findings, and link to evidence. A final conclusion
such as `REVIEW: PASS` or `REVIEW: CHANGES_REQUIRED` makes the result
unambiguous. A reviewer can submit it as `COMMENTED` or a PR comment.
After a new commit, the old review becomes stale until its scope and SHA are
rechecked. If review provenance is missing, record `REVIEW_UNVERIFIED`.
Never call a `COMMENTED` review `APPROVED` in GitHub or bypass a configured
branch rule requiring an approval event, permissions or CI.

## Decisions for a new agent

The following cases specify the safe next action. They are checklists for
human and automated review, not evidence that an autonomous agent was executed.

| Scenario | Required decision |
| --- | --- |
| 01 No assigned task | Inspect live Issues, dependencies, PRs and select one ready stage |
| 02 Several open PRs | Prefer the highest-impact unblocked compatible unfinished PR |
| 03 Merged but not deployed | Verify deployment SHA and failure; do not claim completion |
| 04 Test fails | Reproduce and repair root cause; retain regression coverage |
| 05 Duplicate configuration | Extend canonical configuration; do not add another |
| 06 New dependency proposed | Justify and verify license, supply chain and compatibility |
| 07 Architecture change | Read `docs/architecture.md`; write an ADR for a material decision |
| 08 Research experiment | Read protocol, data policy, analysis and reproducibility contract |
| 09 Another agent owns Issue | Coordinate or select another task, do not overwrite |
| 10 Stale documentation | Compare code/tests/history; repair canonical description |
| 11 Six PRs already active | Close ready PRs or mark blocked, avoid starting more |
| 12 Public repository workflow | Use isolated free hosted jobs and minimal tokens |
| 13 Private runner requested | Do not run untrusted PR code or unapproved workloads |
| 14 Participant data in output | Block publication, sanitize and verify rights |
| 15 Conflicting instructions | Apply safety hierarchy and escalate irreconcilable conflict |
| 16 Branch cleanup | Confirm merge and ownership before deletion |
| 17 Shared package requested | Require real reuse and stable boundaries before extraction |
| 18 Cannot run tests | Record `NOT_RUN` with reason; no fabricated `PASS` |
| 19 Persistent project decision | Record in canonical documentation or ADR, not a transient chat |
| 20 GitHub tools unavailable | Preserve local work and mark remote state unknown or blocked |

## Handoff receipt

Record repository, Issue/PR, full commit SHA, file scope, test commands and
results, environment, unresolved risks, deployment status (if relevant),
and the next actionable step. Do not invent tests or timestamps.
