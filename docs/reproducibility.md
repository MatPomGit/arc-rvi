# Reproducibility contract

Every reported run should include:
- `run_id`, UTC timestamp, research question and evidence level.
- Source revision and unmodified configuration checksum.
- Dataset revision, provenance, usage permissions and partition specification.
- Environment: OS, Python, simulator/robot firmware, devices and calibration.
- PRNG seeds, trial order, experimental conditions and controlled variables.
- Per-trial results, failures and raw measurement metadata.
- A deterministic script generating tables/figures from the recorded outputs.

The `rvi plan` example writes synthetic output; it is not an experiment result.
Keep large/private artifacts off Git. Publish safe manifests and hashes only.
