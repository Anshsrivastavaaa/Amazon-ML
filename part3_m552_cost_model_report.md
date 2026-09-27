# M5.5.2 Downstream Candidate Cost and Resource Envelope

## Scope and boundaries

This is an artifact-only modeling checkpoint. No candidate-generation
experiment was run and no M4, M5.2, M5.3.3, M5.3.4, or M5.4 artifact was
modified. The machine-readable model is
[part3_m552_cost_model.json](data/processed/part3_m552_cost_model.json).

The model uses the measured threshold-250 cumulative results normalized in
M5.5.1. It does not extrapolate cumulative behavior to lower thresholds.
Modeled downstream scoring values are scenario estimates, not measured
matcher performance.

## Measured inputs

Inputs are taken from
[part3_m551_evidence_normalized.json](data/processed/part3_m551_evidence_normalized.json)
and its source report:

- candidate-pair totals;
- average, median, P95, P99, and maximum candidates per S1;
- zero-candidate S1 count;
- blocking wall runtime and CPU runtime;
- M5.4 measured peak RSS reference.

S2 and S3 remain separate. The measured blocking peak RSS references are
7,228.855 MB for M5.4.3 and 7,173.832 MB for M5.4.4. These are blocking
process measurements, not downstream matcher memory requirements.

## Scenario assumptions

The following values are explicit hypothetical parameters:

| Scenario | Assumed scoring time/candidate | Assumed additional memory/scored pair |
|---|---:|---:|
| low | 0.1 ms | 128 bytes |
| mid | 1.0 ms | 512 bytes |
| high | 5.0 ms | 2,048 bytes |

These assumptions are not empirical measurements. The model exposes them in
the JSON artifact so they can be replaced without changing the measured
inputs.

## Candidate-generation cost — measured

Candidate-generation cost is kept separate from modeled scoring cost.
Measured cumulative blocking runtimes are:

| Target | Stage | Candidate pairs | Blocking wall seconds | Blocking CPU seconds |
|---|---|---:|---:|---:|
| S2 | M4 | 14,999,941 | 65.310 | 64.063 |
| S2 | M4 ∪ M5.2 | 39,196,644 | 163.062 | 159.734 |
| S2 | M4 ∪ M5.2 ∪ M5.3.3 | 48,053,985 | 319.973 | 312.203 |
| S2 | Full union | 48,053,985 | 443.278 | 432.672 |
| S3 | M4 | 15,029,807 | 66.603 | 65.406 |
| S3 | M4 ∪ M5.2 | 39,106,086 | 167.819 | 164.562 |
| S3 | M4 ∪ M5.2 ∪ M5.3.3 | 47,725,936 | 339.701 | 329.406 |
| S3 | Full union | 47,725,936 | 472.372 | 459.656 |

These measured blocking values are not added to, or combined with, the
modeled downstream scoring estimates.

## Modeled downstream scoring outputs

Formula for total scoring time:

`candidate_pairs * assumed_scoring_time_ms_per_candidate / 1000`

The scoring CPU-time equivalent uses the same arithmetic as a workload
estimate. It is not measured CPU time and assumes no parallelism or
overhead adjustment.

### S2

| Stage | Candidate pairs | Low / mid / high total scoring seconds | Low / mid / high temporary memory GB |
|---|---:|---:|---:|
| M4 | 14,999,941 | 1,499.994 / 14,999.941 / 74,999.705 | 1.788132 / 7.152529 / 28.610117 |
| M4 ∪ M5.2 | 39,196,644 | 3,919.664 / 39,196.644 / 195,983.220 | 4.672604 / 18.690416 / 74.761665 |
| M4 ∪ M5.2 ∪ M5.3.3 | 48,053,985 | 4,805.399 / 48,053.985 / 240,269.925 | 5.728481 / 22.913926 / 91.655703 |
| Full union | 48,053,985 | 4,805.399 / 48,053.985 / 240,269.925 | 5.728481 / 22.913926 / 91.655703 |

### S3

| Stage | Candidate pairs | Low / mid / high total scoring seconds | Low / mid / high temporary memory GB |
|---|---:|---:|---:|
| M4 | 15,029,807 | 1,502.981 / 15,029.807 / 75,149.035 | 1.791693 / 7.166770 / 28.667082 |
| M4 ∪ M5.2 | 39,106,086 | 3,910.609 / 39,106.086 / 195,530.430 | 4.661809 / 18.647235 / 74.588940 |
| M4 ∪ M5.2 ∪ M5.3.3 | 47,725,936 | 4,772.594 / 47,725.936 / 238,629.680 | 5.689375 / 22.757500 / 91.029999 |
| Full union | 47,725,936 | 4,772.594 / 47,725.936 / 238,629.680 | 5.689375 / 22.757500 / 91.029999 |

Formula for temporary memory:

`candidate_pairs * assumed_additional_memory_bytes_per_candidate /
1,073,741,824`

This is a modeled temporary allocation estimate only. It excludes model
parameters, interpreter/runtime overhead, batching, allocator behavior,
input/output storage, and parallel workers.

## Tail workload indicators — measured and modeled separately

Tail counts are measured candidates per S1. The corresponding scoring times
below use the **mid scenario only** (1.0 ms/candidate), so they are estimates.

| Target | Stage | Measured P95 / P99 / max candidates per S1 | Modeled mid-scenario P95 / P99 / max seconds per S1 | Zero-candidate S1 |
|---|---|---:|---:|---:|
| S2 | M4 | 168 / 249 / 684 | 0.168 / 0.249 / 0.684 | 240,031 |
| S2 | M4 ∪ M5.2 | 296 / 434 / 1,115 | 0.296 / 0.434 / 1.115 | 111,444 |
| S2 | M4 ∪ M5.2 ∪ M5.3.3 | 328 / 458 / 1,115 | 0.328 / 0.458 / 1.115 | 82,780 |
| S2 | Full union | 328 / 458 / 1,115 | 0.328 / 0.458 / 1.115 | 82,780 |
| S3 | M4 | 168 / 249 / 724 | 0.168 / 0.249 / 0.724 | 242,191 |
| S3 | M4 ∪ M5.2 | 296 / 434 / 1,115 | 0.296 / 0.434 / 1.115 | 111,968 |
| S3 | M4 ∪ M5.2 ∪ M5.3.3 | 327 / 457 / 1,115 | 0.327 / 0.457 / 1.115 | 83,737 |
| S3 | Full union | 327 / 457 / 1,115 | 0.327 / 0.457 / 1.115 | 83,737 |

The average candidates/S1 does not describe every entity: the measured
median is zero for M4, while the P95, P99, and maximum are substantially
larger. Zero-candidate counts also remain material. These are workload
distribution facts, not claims about matcher accuracy.

## Metric definitions and provenance

| Modeled metric | Parameter/unit | Numerator | Denominator | Formula | Assumption/source |
|---|---|---|---|---|---|
| Total downstream scoring time | seconds | candidate pairs × scoring milliseconds | 1,000 ms/second | `candidate_pairs × scoring_ms / 1000` | Scoring-time scenarios above; candidate pairs from M5.5.1 |
| Scoring CPU-time equivalent | seconds | same as total scoring time | 1,000 ms/second | same arithmetic | Scenario estimate, not measured CPU |
| Temporary memory | GB | candidate pairs × bytes/pair | 1,073,741,824 bytes/GB | `candidate_pairs × bytes_per_pair / 1073741824` | Memory scenarios above; excludes overhead |
| Tail scoring time | seconds/S1 | tail candidates/S1 × scoring milliseconds | 1,000 ms/second | `tail_candidates × scoring_ms / 1000` | P95/P99/max measured in M5.5.1; time is modeled |
| Candidate workload scale | pairs or candidates/S1 | measured candidate count/distribution | not applicable | direct measured input | M5.5.1 normalized artifact |

## Synthetic/unit validation

The artifact validates the formula implementation with a small fixture:

- 1,000 candidate pairs;
- 2 ms assumed scoring time per candidate;
- 512 bytes assumed additional memory per pair;
- expected scoring time: `1,000 × 2 / 1,000 = 2.0 seconds`;
- expected temporary memory:
  `1,000 × 512 / 1,073,741,824 = 0.0004768371582 GB`.

This validation uses no source dataset.

## Limitations and interpretation boundaries

- Downstream scoring time and memory are scenario estimates, not benchmarked
  matcher performance.
- No empirical per-candidate scoring time or per-pair memory value exists in
  the supplied evidence.
- Temporary memory estimates omit fixed model memory, batching, allocator
  overhead, serialization, and concurrency.
- Scoring CPU-time equivalent is not the measured blocking CPU runtime.
- M5.4 peak RSS is measured blocking memory, not a downstream matcher
  requirement.
- Results cover threshold 250 only and do not establish lower-threshold
  cumulative behavior.
- This checkpoint does not select, rank, recommend, or identify any
  architecture as best, optimal, preferred, or final.
