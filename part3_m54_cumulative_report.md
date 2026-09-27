# M5.4.5 Cumulative Candidate-Generation Analysis

## Scope

This report consolidates the committed M5.4.2, M5.4.3, and M5.4.4 artifacts.
No candidate-generation experiment was rerun.

All reported stages use the fixed 20% Source-1 entity-level validation split
(`seed=42`, 441,365 entities) and threshold 250. Candidate overlap and
marginal recovery come from explicit per-S1 candidate identities, not from
combining standalone recall values.

Source artifacts and checkpoints:

- M5.4.2: [`part3_m54_m4_m52_union_results.json`](data/processed/part3_m54_m4_m52_union_results.json), commits `f5bb10f`, `23da36b`
- M5.4.3: [`part3_m54_m4_m52_m533_union_results.json`](data/processed/part3_m54_m4_m52_m533_union_results.json), commit `acdb744`
- M5.4.4: [`part3_m54_m4_m52_m533_m534_union_results.json`](data/processed/part3_m54_m4_m52_m533_m534_union_results.json), commit `31224cb`

## Measured cumulative results

### S2

| Cumulative stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 0.999993250 | 65.310 | 64.063 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 0.999982361 | 163.062 | 159.734 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 319.973 | 312.203 |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 443.278 | 432.672 |

### S3

| Cumulative stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 0.999993557 | 66.603 | 65.406 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 0.999983237 | 167.819 | 164.562 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 339.701 | 329.406 |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 472.372 | 459.656 |

## Marginal additions from measured identities

### S2

| Addition | New true pairs | New complete entities | Candidate-pair increase | Marginal pair-recall gain | Marginal candidate cost | Previously missed pairs | Previous misses recovered |
|---|---:|---:|---:|---:|---:|---:|---:|
| M5.2 added to M4 | 212,979 | 111,236 | 24,196,703 | 0.288083 | 113.611 | 451,100 | 47.213% |
| M5.3.3 added to M4 ∪ M5.2 | 41,075 | 21,119 | 8,857,341 | 0.055559 | 215.638 | 238,121 | 17.250% |
| M5.3.4 added to M4 ∪ M5.2 ∪ M5.3.3 | 0 | 0 | 0 | 0.000000 | None | 197,046 | 0.000% |

### S3

| Addition | New true pairs | New complete entities | Candidate-pair increase | Marginal pair-recall gain | Marginal candidate cost | Previously missed pairs | Previous misses recovered |
|---|---:|---:|---:|---:|---:|---:|---:|
| M5.2 added to M4 | 218,433 | 106,385 | 24,076,279 | 0.276689 | 110.223 | 487,372 | 44.819% |
| M5.3.3 added to M4 ∪ M5.2 | 44,056 | 21,547 | 8,619,850 | 0.055806 | 195.657 | 268,939 | 16.381% |
| M5.3.4 added to M4 ∪ M5.2 ∪ M5.3.3 | 0 | 0 | 0 | 0.000000 | None | 224,883 | 0.000% |

Candidate cost is added candidate pairs divided by newly recovered true
pairs. It is `None` when no new true pair is recovered.

## Resource and reproducibility information

The largest measured peak RSS was approximately 7,228.86 MB in M5.4.3;
M5.4.4 reported approximately 7,173.83 MB. Experiments processed S2 and S3
sequentially, and disk space remained stable. The M5.4.5 checkpoint itself
performed no large run.

## Interpretation

### Measured results

- M5.2 added substantial measured recovery to M4 for both targets.
- M5.3.3 added further measured recovery after the M4 ∪ M5.2 union.
- At threshold 250, M5.3.4 added zero candidate pairs, zero newly recovered
  true pairs, and zero newly complete entities for both S2 and S3.

### Derived metrics

The marginal recall gains, candidate-pair increases, candidate costs, and
previous-miss recovery percentages above are calculated from candidate
identity differences recorded by the M5.4 artifacts.

### Observed complementarity and overlap

M5.2 and M5.3.3 show measured incremental recovery beyond their preceding
cumulative sets. The threshold-250 M5.3.4 candidate identities were fully
contained in the preceding cumulative candidate sets for both targets in this
evaluation.

### Limitations

- The primary M5.4 analysis covers threshold 250 only.
- Lower thresholds 5, 10, 25, 50, and 100 were intentionally not run here;
  no result is inferred for them.
- Results are specific to the fixed validation split and approved semantics.
- No final blocking architecture is selected by this report.

### Questions for M5.5

M5.5 should weigh cumulative recall, candidate volume, runtime, memory, and
operational complexity across the measured families, and decide whether any
additional sensitivity analysis is justified. M5.4 does not make that
architecture decision.
