# M5.5.5 Blocking Trade-off Evidence Handoff

## Scope and evidence status

This report consolidates committed M5.4 and M5.5 evidence for handoff to the
next decision checkpoint. It is a report-only checkpoint: no candidate sets
were generated, no experiment was run, and no implementation was changed.
The report makes no architecture selection.

All cumulative identity-union results use the fixed 20% Source-1
entity-level validation split (`seed=42`, 441,365 validation Source-1
entities), approved blocking semantics, and actual per-S1 candidate
identities. S2 and S3 are kept separate.

Evidence labels used below:

- **Measured:** directly recorded by a committed experiment or artifact.
- **Derived:** calculated from measured artifact fields with the stated
  formula.
- **Modeled:** scenario output based on explicit M5.5.2 assumptions.
- **Hypothesis:** an architecture concept or unverified interpretation.
- **Open question:** unresolved for a later decision checkpoint.

## Executive evidence summary

- Cumulative identity unions were measured only at thresholds **5, 25, and
  250**.
- Thresholds **10, 50, and 100 were not cumulatively evaluated**. No result
  is extrapolated to those thresholds.
- At threshold 250, M4 plus M5.2 increased pair recall from 0.389827 to
  0.677909 for S2 and from 0.382646 to 0.659335 for S3.
- Adding M5.3.3 at threshold 250 produced additional measured recovery:
  41,075 S2 pairs and 44,056 S3 pairs.
- Threshold 5 and threshold 25 produced smaller measured candidate additions
  than threshold 250, with threshold-specific recovery and cost values.
- M5.3.4 added zero candidates, zero new true pairs, and zero new complete
  entities at measured thresholds 5, 25, and 250 for both S2 and S3. This is
  not generalized to thresholds 10, 50, or 100.
- Measured blocking RSS increased from the M5.4 reference of approximately
  7.23 GB to approximately 7.62 GB at threshold 5 and 8.44 GB at threshold
  25. Threshold 25 was completed and captured, then further sensitivity
  execution stopped because of resource pressure.
- M5.5.2 downstream scoring and memory values are hypothetical scenarios, not
  measured matcher performance or downstream memory requirements.

## S2 cumulative trade-off table — measured

| Cumulative stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Wall s | CPU s | Source |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 61.103 | 60.234 | M5.5.3 threshold-5 artifact |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 158.469 | 156.031 | M5.5.3 threshold-5 artifact |
| M4 ∪ M5.2 ∪ M5.3.3(5) | 0.680542 | 0.681991 | 39,207,683 | 88.833 | 51 | 296 | 434 | 1,115 | 110,009 | 316.077 | 310.656 | M5.5.3 threshold-5 artifact |
| M4 ∪ M5.2 ∪ M5.3.3(25) | 0.688069 | 0.688344 | 39,380,227 | 89.224 | 51 | 297 | 435 | 1,115 | 106,236 | 392.727 | 386.859 | M5.5.3 threshold-25 artifact |
| M4 ∪ M5.2 ∪ M5.3.3(250) | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 319.973 | 312.203 | M5.5.1/M5.4 artifact |
| Full union at each measured threshold | same as preceding row | same | same | same | same | same | same | same | same | see source reports | see source reports | M5.3.4 identity checks |

## S3 cumulative trade-off table — measured

| Cumulative stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Wall s | CPU s | Source |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 65.772 | 65.156 | M5.5.3 threshold-5 artifact |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 164.969 | 163.313 | M5.5.3 threshold-5 artifact |
| M4 ∪ M5.2 ∪ M5.3.3(5) | 0.662014 | 0.654098 | 39,116,510 | 88.626 | 51 | 296 | 434 | 1,115 | 110,504 | 325.248 | 321.250 | M5.5.3 threshold-5 artifact |
| M4 ∪ M5.2 ∪ M5.3.3(25) | 0.669517 | 0.660533 | 39,284,812 | 89.008 | 51 | 296 | 434 | 1,115 | 106,782 | 410.563 | 404.531 | M5.5.3 threshold-25 artifact |
| M4 ∪ M5.2 ∪ M5.3.3(250) | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 339.701 | 329.406 | M5.5.1/M5.4 artifact |
| Full union at each measured threshold | same as preceding row | same | same | same | same | same | same | same | same | see source reports | see source reports | M5.3.4 identity checks |

## Marginal contribution table — measured identities

Marginal candidate cost is `added candidate pairs / newly recovered true
pairs`. Previous-miss recovery is the newly recovered pair count divided by
the true pairs missed by the preceding cumulative stage.

| Target | Addition | New pairs | New complete entities | Added candidates | Pair-recall gain | Candidate cost | Previous misses recovered | Source |
|---|---|---:|---:|---:|---:|---:|---:|---|
| S2 | M5.2 after M4 | 212,979 | 111,236 | 24,196,703 | 0.288083 | 113.611 | 47.213% | M5.5.1/M5.4 |
| S2 | M5.3.3(5) after M4 ∪ M5.2 | 1,946 | 1,063 | 11,039 | 0.002633 | 5.673 | 0.817% | threshold-5 artifact |
| S2 | M5.3.3(25) after M4 ∪ M5.2 | 7,511 | 3,867 | 183,583 | 0.010160 | 24.442 | 3.154% | threshold-25 artifact |
| S2 | M5.3.3(250) after M4 ∪ M5.2 | 41,075 | 21,119 | 8,857,341 | 0.055559 | 215.638 | 17.250% | M5.5.1/M5.4 |
| S2 | M5.3.4 after preceding union | 0 | 0 | 0 | 0.000000 | None | 0.000% | M5.3.4 identity checks |
| S3 | M5.2 after M4 | 218,433 | 106,385 | 24,076,279 | 0.276689 | 110.223 | 44.819% | M5.5.1/M5.4 |
| S3 | M5.3.3(5) after M4 ∪ M5.2 | 2,115 | 1,096 | 10,424 | 0.002679 | 4.929 | 0.786% | threshold-5 artifact |
| S3 | M5.3.3(25) after M4 ∪ M5.2 | 8,038 | 3,936 | 178,726 | 0.010182 | 22.235 | 2.989% | threshold-25 artifact |
| S3 | M5.3.3(250) after M4 ∪ M5.2 | 44,056 | 21,547 | 8,619,850 | 0.055806 | 195.657 | 16.381% | M5.5.1/M5.4 |
| S3 | M5.3.4 after preceding union | 0 | 0 | 0 | 0.000000 | None | 0.000% | M5.3.4 identity checks |

## Threshold sensitivity — measured cumulative identity unions

| Target | Threshold | M5.3.3 new pairs | M5.3.3 added candidates | M5.3.3 candidate cost | M5.3.4 new pairs | M5.3.4 added candidates | Cumulative status |
|---|---:|---:|---:|---:|---:|---:|---|
| S2 | 5 | 1,946 | 11,039 | 5.673 | 0 | 0 | measured |
| S2 | 25 | 7,511 | 183,583 | 24.442 | 0 | 0 | measured; resource stop afterward |
| S2 | 250 | 41,075 | 8,857,341 | 215.638 | 0 | 0 | measured |
| S3 | 5 | 2,115 | 10,424 | 4.929 | 0 | 0 | measured |
| S3 | 25 | 8,038 | 178,726 | 22.235 | 0 | 0 | measured; resource stop afterward |
| S3 | 250 | 44,056 | 8,619,850 | 195.657 | 0 | 0 | measured |

Thresholds 10, 50, and 100 were not cumulatively evaluated. Standalone
threshold rows for those values are not cumulative-union evidence.

## Resource and scalability envelope — measured

| Evidence | Peak RSS | Runtime detail | Disk detail |
|---|---:|---|---|
| M5.4 threshold-250 reference | ~7,228.855 MB | S2/S3 sequential; see M5.4 report | Stable |
| Threshold 5 | 7,621.754 MB | S2 437.041 s wall / 429.969 s CPU; S3 453.385 / 447.656 | Post-run free disk ~431.583 GB |
| Threshold 25 | 8,438.969 MB | S2 512.613 s wall / 504.922 s CPU; S3 537.889 / 529.500 | Post-run free disk ~431.780 GB |

Threshold 25 completed and its result was captured. The checkpoint stopped
before further sensitivity execution because peak RSS exceeded the prior
M5.4 reference and increased again from threshold 5. This is a resource-stop
boundary, not an experiment failure. No threshold 100, 50, or 10 run was
executed, and thresholds 5 and 25 were not rerun.

Measured blocking RSS is a process-level observation. It is not a downstream
matcher memory requirement.

## Downstream cost-model assumptions and limitations — modeled

M5.5.2 applies explicit scenarios to measured threshold-250 candidate counts:

| Scenario | Scoring time assumption | Additional memory assumption |
|---|---:|---:|
| Low | 0.1 ms/candidate | 128 bytes/scored pair |
| Mid | 1.0 ms/candidate | 512 bytes/scored pair |
| High | 5.0 ms/candidate | 2,048 bytes/scored pair |

Modeled scoring time is:

`candidate_pairs × assumed_scoring_time_ms / 1000`

Modeled temporary memory is:

`candidate_pairs × assumed_bytes_per_pair / 1,073,741,824`

These are scenario calculations, not matcher benchmarks. They exclude fixed
model memory, batching, allocator behavior, serialization, concurrency, and
input/output storage. The modeled values must not be added to measured
blocking RSS or interpreted as production performance.

## Architecture hypotheses — neutral handoff

The following concepts are hypotheses supported by different portions of the
measured evidence. They are not ordered or scored.

| Concept | Measured evidence | Candidate scale and resource implications | Assumptions and evidence gaps | Future validation |
|---|---|---|---|---|
| M4 only | Baseline S2/S3 recall and candidate distributions are measured. | About 15.0M candidates per target; lower measured candidate totals than the cumulative unions. | Does not recover pairs missed by M4; downstream matching behavior is unmeasured. | Benchmark the downstream matcher and inspect missed entities. |
| M4 ∪ M5.2 | Adds 212,979 S2 and 218,433 S3 pairs beyond M4 at threshold 250. | About 39.1–39.2M candidates; P99 434 and maximum 1,115. | Candidate overlap and cost are split-specific; downstream cost is modeled only. | Measure matcher runtime, memory, and quality on actual identities. |
| M4 ∪ M5.2 ∪ M5.3.3 | Adds measured recovery at thresholds 5, 25, and 250. | Added candidates range from 10,424–11,039 at threshold 5 to 8.62–8.86M at threshold 250 across targets. | Thresholds 10, 50, and 100 lack cumulative results; threshold behavior is not extrapolated. | Any additional threshold or matcher validation requires explicit approval. |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | M5.3.4 adds zero candidates, pairs, and complete entities at measured thresholds 5, 25, and 250. | Candidate identities equal the preceding M5.3.3 stage at those thresholds; generation still has measured runtime overhead. | The zero result is not established for unmeasured thresholds, other splits, or production data. | Review implementation overhead and downstream integration; any rerun needs approval. |
| Threshold-sensitive M5.3.3 variants | Thresholds 5 and 25 have measured cumulative results in addition to threshold 250. | Threshold 25 has more measured recovery and candidate growth than threshold 5, and higher measured RSS. | These observations do not establish behavior at thresholds 10, 50, or 100. | Use only if a later checkpoint authorizes further sensitivity work. |
| Optional M5.3.4 inclusion or exclusion | Zero incremental contribution is measured at 5, 25, and 250. | No measured candidate-volume increase at those thresholds, but generation overhead remains part of the observed process. | No cumulative evidence exists for unmeasured thresholds or downstream quality effects. | Determine whether implementation and integration costs justify further investigation. |

## Evidence gaps

- No cumulative identity-union result exists for thresholds 10, 50, or 100.
- No downstream matcher benchmark measures actual scoring time, peak memory,
  batching behavior, throughput, or quality.
- M5.4 and M5.5 results use one fixed validation split and approved
  semantics; generalization to the competition test set is unmeasured.
- Standalone M3/M4/M5.2/M5.3 recall cannot establish cumulative overlap or
  complementarity without candidate identities.
- Zero-candidate and incompletely matched S1 entities remain material in all
  measured cumulative stages.
- The resource envelope is process-specific and does not define a hardware
  limit or downstream matcher budget.
- M5.3.4's zero contribution is measured only at thresholds 5, 25, and 250.

## Open questions for the next decision stage

These questions are intentionally unresolved:

1. What candidate volume is acceptable for downstream pair matching?
2. What wall-time, CPU-time, peak-RSS, disk, and batching envelope is
   acceptable?
3. Do the measured threshold-5 and threshold-25 M5.3.3 additions justify
   their measured candidate costs under an actual matcher?
4. Is additional threshold sensitivity warranted despite the observed RSS
   growth, and what explicit resource ceiling would govern it?
5. Does M5.3.4 require additional investigation despite zero measured
   incremental contribution at the tested thresholds?
6. Which downstream matcher benchmark and quality metrics are required before
   selecting an architecture?
7. How should zero-candidate and incompletely matched S1 entities be handled
   in downstream processing and evaluation?
8. Which measured candidate identities and provenance must be retained for
   reproducible downstream comparison?

## Proposed next experiments for explicit approval

No experiment is executed by this checkpoint. If a later checkpoint authorizes
experiments, the minimum evidence needed to resolve the open questions is:

1. **Downstream matcher benchmark:** run the candidate identities from the
   measured cumulative stages separately for S2 and S3. Measure match quality,
   pair/entity recall after matching, wall time, CPU time, peak RSS,
   throughput, batch behavior, and zero-candidate handling. Keep blocking
   RSS separate from matcher RSS.
2. **Measured-stage identity replay:** replay the already captured threshold
   5, 25, and 250 candidate identities without regenerating them, if the
   matcher requires a common serialized input format. Validate identity counts
   and provenance before scoring.
3. **Resource-boundary validation:** only if the next decision checkpoint
   determines that unmeasured thresholds are necessary, define a hard RSS,
   runtime, and disk ceiling before considering any threshold 10, 50, or 100
   experiment. Do not infer results from the existing threshold rows.

Each proposed experiment requires separate approval, Python 3.11, sequential
S2/S3 processing, explicit stopping criteria, and artifact validation.

## Provenance

Primary committed sources:

- M5.4 cumulative artifacts and
  [part3_m54_cumulative_report.md](part3_m54_cumulative_report.md);
- M5.5.1 normalized evidence and
  [part3_m551_evidence_normalized_report.md](part3_m551_evidence_normalized_report.md);
- M5.5.2 model and
  [part3_m552_cost_model_report.md](part3_m552_cost_model_report.md);
- M5.5.3 threshold-5 evidence and
  [part3_m553_threshold5_report.md](part3_m553_threshold5_report.md);
- M5.5.3 threshold-25 evidence and
  [part3_m553_threshold25_resource_stop_report.md](part3_m553_threshold25_resource_stop_report.md);
- M5.5.4 comparison and
  [part3_m554_architecture_hypothesis_report.md](part3_m554_architecture_hypothesis_report.md).

This handoff preserves the distinction between measured evidence, derived
arithmetic, modeled scenarios, hypotheses, and unresolved questions. It makes
no architecture decision.
