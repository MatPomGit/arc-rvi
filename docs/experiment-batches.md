# Immutable exploratory experiment batches

This is the first **software-only** shared runner for ARC-RVI. It supports
Study 01 fixture smoke suites and **exploratory** generated planar scenes with
explicit development or pilot partitions. It cannot run physical experiments,
cannot access the generated holdout partition and does not certify a frozen
confirmation protocol. Remaining cross-study adapters belong to [Issue #16](https://github.com/MatPomGit/arc-rvi/issues/16).

## Offline usage

From the repository with an editable installation:

```bash
rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/conditions
rvi batch --manifest results/conditions/manifest.json --partition pilot --output-dir results/study01_batch
rvi batch --manifest results/conditions/manifest.json --partition pilot --output-dir results/study01_batch --resume
```

For a fixture correctness smoke suite, which is never treated as simulation
evidence:

```bash
rvi batch --suite simulation/suites/fixture_smoke.json --output-dir results/fixture_batch
```

Create the parent `results/` directory locally before running these commands.
The runner refuses existing directories except under `--resume`. Resume
**revalidates** the selected input SHA-256 hashes, recomputes the benchmark,
checks source provenance, receipt and stored artifact hashes. It never writes
to an existing batch. A mismatched input, corrupted file or extra artifact
causes a refusal. No background jobs, workers, scheduler, external services or
robot-control adapters are invoked.

## Artifacts

A batch creates three files:

| File | Contract |
| --- | --- |
| `trials.json` | One row for each registered scene × method with pairing, nested replicate, group identity, condition, terminal status/failure reason, named metrics and model attempts |
| `summary.json` | Independent family/fixture counts, denominators, per-method outcomes, terminal-status totals, model and evidence type |
| `receipt.json` | Input and suite hashes, source/package provenance, artifact byte size/SHA-256, start/end UTC timestamps, missing seed-domain labels and output classification |

`trials.json` and `summary.json` are byte-for-byte deterministic for an
unchanged source tree and input. `receipt.json` contains measured wall-clock
timestamps and is *not* byte-identical across separately executed batches.
Model elapsed time is kept distinct from host wall time.

There are no inferred sensor/method/analysis seeds: absent domains remain
explicit `null` and are listed as uncertified. The source revision,
package-source SHA-256, Python version and environment identify software
provenance, including local source edits. Neither resume nor hashes replace
a secure external archival or registry/signature service.

## Isolation, failure accounting and limitations

Only metadata are inspected for non-selected partitions; only the selected
suite and scene files are opened. Requests for holdout/confirmation partitions
are refused before any benchmark. A fixture cannot be passed as a simulation
manifest and a standalone geometric suite cannot bypass split validation.
The current source-level model still exposes known geometry to policy baselines;
this is **oracle visibility**, not unknown-scene perception.

Incomplete coverage and model action failures are retained, not dropped.
The current underlying benchmark exposes `completed` and
`algorithm_failure` as terminal states; the broader
`timeout`/`safety_abort`/`measurement_missing`/
`infrastructure_failure` vocabulary is reserved for later study adapters.
A hard process crash does **not** generate a completed trial row. Those gaps,
plus true runtime budgets, dedicated task-specific schemas, independent scene
noise streams and secure sealed confirmation, remain outstanding.

The implementation must not be described as a complete P01–P08 runner or
used to support physical claims. The [reproducibility contract](reproducibility.md)
and [study protocols](../experiments/README.md) define the remaining gates.
