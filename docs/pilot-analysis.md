# Exploratory paired analysis for study 01

This command processes **only** the pilot partition of the seeded planar-geometry
generator. It does not access holdout outcomes or perform physical validation.
It reevaluates the original paired scenes and checks SHA-256 hashes for the
manifest, suites, scenes and trial provenance before summarizing outcomes.

## Reproduction

Run after installing the package from this source checkout:

    rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/study01_conditions
    rvi pilot --manifest results/study01_conditions/manifest.json --output results/study01_pilot_analysis.json

Both commands refuse to overwrite existing outputs. The analysis defaults to
fixed_order as the reference and greedy_distance as the comparator. These are
**software-pilot defaults only**: the confirmatory reference method remains
unselected. To examine an alternative exploratory contrast, supply
--reference and --comparator with distinct registered method IDs. The default
bootstrap seed is 20261026; the reproducible result includes the seed.

## Outcomes and estimand

A completion means **all reference surface patches acquired in the planar
model**, not operational inspection success. Reference geometry is visible to
the evaluated policies. Coverage is area-weighted sampled reference coverage.
Algorithm failures remain in every denominator, with failure counts reported
by method and condition.

For each paired geometry replicate and method, let L denote the nominal
completion or coverage fraction minus the occluded fraction. The displayed
effect is L(comparator) - L(reference). Positive values mean **larger
occlusion-associated loss** for the comparator. Effects are first averaged
within each geometry family, then averaged equally across families.
Replicate seeds and individual acquisitions are not independent families.

The fixed-template example contains **two pilot families, six pairs and 36 method trials**
and reports descriptive contrasts without confidence intervals. The separately
[sampled-geometry example](population.md) contains **12 pilot families, 24
pairs and 144 method trials**, for which the existing analyzer computes an
exploratory family-resampled interval. Neither design supports physical or
confirmatory inference. Code for a deterministic 10,000-resample percentile bootstrap exists
for exploratory datasets with at least eight sampled model families; this
threshold is a conservative software guard, **not** a sample-size calculation
or a guarantee of correct population coverage. Cluster resampling is at the
family level and retains paired method/condition comparisons.

## Research gates

- Do not claim lighting, clutter, unknown geometry, sensor accuracy, robot
  performance, hypothesis confirmation or publication results from this model.
- Do not tune methods or thresholds on holdout data. The public deterministic
  holdout is not a blinded confirmatory dataset.
- Before any confirmation, independently define the sampling population,
  frozen primary contrast, success thresholds, sufficient cluster count,
  calibration and full crossed challenge factors.
- Retain raw benchmark reports externally if needed for later audit. The
  summary records a hash of the transient benchmark report and its source
  provenance; that hash does not by itself archive the report.

See experiments/exp01_benchmark/protocol.md and
experiments/analysis/README.md for the prospective scientific plan.


## Six-cell fuzzy planning pilot

Use the existing population generator and pilot CLI:

    rvi population --spec simulation/conditions/study01_factorial_pilot.json --output-dir results/p01_factorial
    rvi pilot --manifest results/p01_factorial/manifest.json --factorial-fuzzy --output results/p01_factorial_pilot.json

This opt-in mode evaluates the six reference-brightness occlusion/clutter cells,
five planning methods and six pilot families in the example (180 trials).
It verifies pilot membership and hashes, retains complete reports, and refuses
incomplete matrices rather than silently dropping failures. Holdout scene
files are not read. All four fuzzy-versus-reference comparisons are descriptive
and use reference loss minus candidate loss, unlike the legacy pilot sign.
Absolute nominal and challenge success are reported per family. No confidence
interval or confirmatory inference is produced by this mode. The existing
reference/comparator and seed options apply to the legacy pilot only.
The output is a simulation diagnostic, not physical or confirmatory evidence.

## Exploratory difficulty calibration

    rvi pilot --manifest results/p01_factorial/manifest.json --calibrate-factorial --output results/p01_calibration.json

The fixed grid crosses time budgets 2, 3, 4, 6, 8 and 16 seconds with
horizontal camera fields of view 30, 45, 60 and 90 degrees. All five methods
receive identical scene transformations. Only verified reference-brightness
pilot scenes are loaded; original scene files and holdout inputs are unchanged.
The output retains all trials, method-cell success, pooled nominal and challenge
success, family success dispersion, failure counts and paired fuzzy route
sequence disagreements. The original 16 s / 90 degree condition is a control.
This grid is exploratory and does not select a winner or freeze a parameter.
Inspect floor and ceiling effects and family heterogeneity independently of
which method benefits. Do not use the grid to choose a favorable contrast.
The current model remains a known-geometry planar simulation.


## Decision-level mechanism diagnostics

The calibration artifact now retains each fuzzy decision's candidate gain,
normalized cost, predicted duration, urgency, score derivative, adaptive and
fixed rankings and winner margins. Both rankings are computed on the same
state, without changing the executed policy. Counts across both trajectories
are descriptive state visits, not independent observations.

For a higher-gain, higher-cost candidate, the score crossing is
u = 2 - 2.5 * delta_cost / (delta_gain + delta_cost).
A crossing in the open unit interval requires the gain/cost difference ratio
to lie strictly between 0.25 and 1.5. A crossing does not imply a winner
change in the presence of other candidates.

The artifact also contains separate hand-built mechanism fixtures with
budgets 2.5, 5 and 16 seconds. The near view covers one patch, the farther
view covers two; the tight budget produces a deliberately constructed
rank reversal. These fixtures are software checks, not sampled evidence
of comparative effectiveness, and are excluded from calibration denominators.
No holdout or frozen protocol change is involved.


## Separate tradeoff stress population

The calibration artifact also contains a development-only stress population
with seed 20261124: 12 scaled two-view geometry families crossed with two
relative capture overheads, four relative motion budgets and two route orders.
All five policies receive the same 192 cases (960 trials). No case is rejected
or selected according to a policy outcome. The population is deliberately
enriched for coverage/cost conflicts and is not representative of general
inspection geometry. Report it separately from the 4320 factorial trials.
The original 2.5 s mechanism fixture allows both policies to complete:
their predicted elapsed times are 2.2 and 2.4 seconds. A decision reversal
does not itself imply a success difference. Report paired success categories,
including fixed-only and neither, and all raw traces. The stress population
does not change any existing partition or confirmation protocol.


## Exact small-instance oracle and avoidable failure audit

The calibration output includes an evaluator-only exhaustive oracle over all
feasible ordered subsets of at most nine distinct candidate indices. It
uses the same simulator acquisition semantics, including collision, time
budget, rotation and capture cost. Zero-gain transit views are permitted.
A full route witnesses feasibility; absence of any full route proves
infeasibility only within this finite model, not for arbitrary continuous
paths, revisits, real robots or additional candidate poses.

Each case retains the optimal area coverage, elapsed time, ordered view
indices (one-based), minimum full-completion time, and method-level coverage
gaps. Each method failure is classified as avoidable (a full feasible
sequence exists) or infeasible (none exists). AFR divides avoidable failures
by feasible instances; the share among failures has a different denominator.
Empty denominators are null. Factorial and stress populations remain separate.

Retrospective independent audit of artifact 14929105602 (CI 45412033425,
merge checkout 62004a720b76a167a3c48fc76b5aafadce10b584) replayed 7567
recorded acquisition events and checked 97 archive checksums. Of 864
factorial instances, 547 were feasible. Across 4320 policy trials, 188
failures were avoidable and 1585 were infeasible. Both fuzzy and fixed
weight had two avoidable failures, belonging to the same geometry family.
Of 192 stress instances, 120 were feasible; all five policies completed
those 120 and failed the remaining 72. The stress population therefore
has zero avoidable completion failures but nonzero partial-coverage gaps
for some policies. These are exploratory finite-model diagnostics, not
confirmatory inference. No protocol, policy parameters or holdout is changed.
The new implementation requires fresh CI and separate technical review.


## RVI-R05: policy-independent decision-structure population

    rvi decision-population --output results/decision-population.json

This separate development-only population draws eight latent radial
geometry families (seed 20261125). Each has six unequal-area outward-facing
patches, independently jittered camera poses and a fixed randomized view
order. Cross nested six/eight-view candidate sets, 18/55 degree FoV,
and absence/presence of a central circular obstacle. Retain every base
scene and all three budgets (0.8, 1.05, 1.4 times minimum full-route time).
The 100 s reference budget is nonbinding by construction for at most eight
distinct visits. When complete coverage is structurally impossible, use
candidate count times the longest accepted direct edge as a labelled
fallback budget reference, not a ratio to an optimum. All 64 base scenes
and 192 budget cases are retained; no policy is executed during selection
or generation, and no new holdout is accessed or created.

Measure minimum number of covering views without motion, mean pairwise
Jaccard similarity (exclude empty unions), visible fraction, blocked directed
candidate-to-candidate transitions, and exact optimum with and without a
tight budget. For each budget-feasible case, first-action dead-end fraction
is the proportion of immediately admissible first actions that cannot start
any full-completion route. Report null for infeasible cases, not zero.
This is order dependence induced by geometry and timing, not an explicit
precedence constraint. Candidate routes permit zero-gain transit and no
revisits, exactly as the finite reference evaluator. The full report stores
each loadable scene, canonical JSON SHA-256, optimal routes, per-first-view
minimum completion times, and descriptive summaries by family and factor.

An independent prototype audit using the same specified factors yielded
42/64 structurally feasible base scenes, 84/192 budget-feasible cases and
63/84 order-sensitive feasible cases. These are development diagnostics,
not estimates of natural scene prevalence or evidence for a particular
heuristic. The canonical implementation must be verified on fresh CI;
the earlier calibration and stress populations remain separate.


## RVI-R06: stronger non-fuzzy reference policies

    rvi decision-compare --population results/decision-population.json --output results/decision-comparison.json

The input is the complete RVI-R05 development grid. The comparison checks
the canonical scene hashes, factor assignments, geometry and budget,
recomputes the exact oracle and preserves all 192 cases. The original five
policies are unchanged. Four additional known-geometry variants use area
rather than patch count for gain: feasible greedy (maximum immediate area),
gain per cost (maximum immediate area per elapsed second), and receding
horizon 2/3 (maximum final covered area among all feasible prefixes within
the horizon, then minimum elapsed time, shortest prefix, candidate order).
The two greedy variants break ties by lower time and then candidate order;
gain per cost prefers positive-gain zero-duration actions. Lookahead permits
zero-gain transit if its prefix adds coverage, and executes only the first
action. No policy calls the exact evaluator or sees its solution. Planning
uses the same simulator transition and collision/time semantics; rejected
predictions are not executed. Planning CPU time is not charged to the
simulated mission; report predicted transition counts separately, not as
wall-clock latency. The older policies retain their original count-based
gain and failure semantics, so comparisons do not isolate a single feature.

The retrospective independent comparison on verified artifact 14941045859
(population SHA-256 e8cffba110dd20e81f90fd2df7d8f3eb037092663ae4f4ac604eafd790a723c3)
found 70/84 feasible completions for gain per cost, 62 for each of
greedy distance, fixed weight and fuzzy budget, 56 for horizon 3, 41 for
horizon 2 and 17 for feasible greedy. All 108 structurally/budget infeasible
instances remain in coverage summaries. Gain per cost has 14 avoidable
failures, 13 at 1.05 times optimum, and mean coverage gap 1.67 percentage
points over all 192 cases. These are descriptive development results,
not independent trials or a confirmatory comparison. The strong baseline
and residual failure analysis should precede any new fuzzy contribution.


## Retention of independent exploratory audits

Preserve independent audit scripts and their result files in versioned
stage-specific directories under `research/evidence/p01/`, alongside
SHA-256 checksums and source provenance. The RVI-R03 through RVI-R06
historical files are in `research/evidence/p01/rvi-r03-r06/`. Keep raw
archives out of the generated website and never publish holdout or private
information. Do not overwrite historical evidence with a new run.
