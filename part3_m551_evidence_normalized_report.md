# M5.5.1 Evidence Normalization and Trade-off Tables

## Scope

This report normalizes only the committed M5.4 evidence. No candidate sets
were regenerated and no new experiment was run. All cumulative results are
for threshold 250, the fixed 20% Source-1 entity-level validation split,
seed 42, and 441,365 validation Source-1 entities. S2 and S3 are reported
separately.

Source artifacts:

- [`part3_m54_m4_m52_union_results.json`](data/processed/part3_m54_m4_m52_union_results.json) — M5.4.2, commits `f5bb10f`, `23da36b`
- [`part3_m54_m4_m52_m533_union_results.json`](data/processed/part3_m54_m4_m52_m533_union_results.json) — M5.4.3, commit `acdb744`
- [`part3_m54_m4_m52_m533_m534_union_results.json`](data/processed/part3_m54_m4_m52_m533_m534_union_results.json) — M5.4.4, commit `31224cb`
- [`part3_m54_cumulative_report.md`](part3_m54_cumulative_report.md) — M5.4.5, commit `1e4070b`

The machine-readable normalized artifact is
[`part3_m551_evidence_normalized.json`](data/processed/part3_m551_evidence_normalized.json).

## S2 cumulative trade-off table — measured

| Cumulative stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 0.999993250 | 65.310 | 64.063 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 0.999982361 | 163.062 | 159.734 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 319.973 | 312.203 |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 443.278 | 432.672 |

## S3 cumulative trade-off table — measured

| Cumulative stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 0.999993557 | 66.603 | 65.406 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 0.999983237 | 167.819 | 164.562 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 339.701 | 329.406 |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 472.372 | 459.656 |

## Marginal contribution table — measured identity differences

| Target | Addition | New true pairs | New complete entities | Added candidate pairs | Marginal pair-recall gain | Marginal candidate cost | Previously missed pairs | Previous misses recovered |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S2 | M5.2 added to M4 | 212,979 | 111,236 | 24,196,703 | 0.288083 | 113.611 | 451,100 | 47.213% |
| S2 | M5.3.3 added to M4 ∪ M5.2 | 41,075 | 21,119 | 8,857,341 | 0.055559 | 215.638 | 238,121 | 17.250% |
| S2 | M5.3.4 added to prior union | 0 | 0 | 0 | 0.000000 | None | 197,046 | 0.000% |
| S3 | M5.2 added to M4 | 218,433 | 106,385 | 24,076,279 | 0.276689 | 110.223 | 487,372 | 44.819% |
| S3 | M5.3.3 added to M4 ∪ M5.2 | 44,056 | 21,547 | 8,619,850 | 0.055806 | 195.657 | 268,939 | 16.381% |
| S3 | M5.3.4 added to prior union | 0 | 0 | 0 | 0.000000 | None | 224,883 | 0.000% |

The marginal values above are measured or directly recorded in the M5.4
artifacts. Marginal candidate cost is `added candidate pairs / new true
pairs`, and is `None` when no new true pair is recovered.

## Candidate-growth table — derived

| Target | Addition | Earlier candidates | Later candidates | Numerator | Denominator | Candidate growth |
|---|---|---:|---:|---:|---:|---:|
| S2 | M5.2 added to M4 | 14,999,941 | 39,196,644 | 24,196,703 | 14,999,941 | 1.6131198783 |
| S2 | M5.3.3 added to M4 ∪ M5.2 | 39,196,644 | 48,053,985 | 8,857,341 | 39,196,644 | 0.2259719225 |
| S2 | M5.3.4 added to prior union | 48,053,985 | 48,053,985 | 0 | 48,053,985 | 0.0000000000 |
| S3 | M5.2 added to M4 | 15,029,807 | 39,106,086 | 24,076,279 | 15,029,807 | 1.6019020737 |
| S3 | M5.3.3 added to M4 ∪ M5.2 | 39,106,086 | 47,725,936 | 8,619,850 | 39,106,086 | 0.2204222125 |
| S3 | M5.3.4 added to prior union | 47,725,936 | 47,725,936 | 0 | 47,725,936 | 0.0000000000 |

Formula: `(later-stage candidate pairs - earlier-stage candidate pairs) /
earlier-stage candidate pairs`. Numerator and denominator are cumulative
candidate-pair fields from the applicable M5.4 artifacts.

## Derived cost-efficiency metrics

| Target | Addition | Recall gain per million added candidates | Numerator | Denominator |
|---|---|---:|---|---|
| S2 | M5.2 added to M4 | 0.0119058679 | marginal pair-recall gain = 0.2880827488 | added candidates / 1,000,000 = 24.196703 |
| S2 | M5.3.3 added to M4 ∪ M5.2 | 0.0062726500 | marginal pair-recall gain = 0.055559 | added candidates / 1,000,000 = 8.857341 |
| S2 | M5.3.4 added to prior union | None | 0 | 0 |
| S3 | M5.2 added to M4 | 0.0114921849 | marginal pair-recall gain = 0.2766890493 | added candidates / 1,000,000 = 24.076279 |
| S3 | M5.3.3 added to M4 ∪ M5.2 | 0.0064740951 | marginal pair-recall gain = 0.0558057288 | added candidates / 1,000,000 = 8.619850 |
| S3 | M5.3.4 added to prior union | None | 0 | 0 |

Formula: `marginal pair-recall gain / (added candidate pairs / 1,000,000)`.
The numerator is the artifact's marginal pair-recall field. The denominator
is the artifact's marginal candidate-pair field divided by 1,000,000. The
metric is `None` when no candidate pairs were added.

## Derived-metric definitions and provenance

| Metric | Numerator | Denominator | Formula | Source artifact/source fields |
|---|---|---|---|---|
| Marginal pair-recall gain | Newly recovered true pairs | Total ground-truth true pairs | `newly recovered true pairs / total ground-truth true pairs` | Applicable M5.4 JSON; `marginal_pair_recall`, `new_recovered_pairs` |
| Marginal candidate cost | Added candidate pairs | Newly recovered true pairs | `added candidate pairs / newly recovered true pairs` | Applicable M5.4 JSON; `marginal_candidate_pairs`, `marginal_candidate_cost`, `new_recovered_pairs` |
| Recall gain per million added candidates | Marginal pair-recall gain | Added candidate pairs / 1,000,000 | `marginal pair-recall gain / (added candidate pairs / 1,000,000)` | Applicable M5.4 JSON; `marginal_pair_recall`, `marginal_candidate_pairs` |
| Candidate growth | Later candidate pairs - earlier candidate pairs | Earlier candidate pairs | `(later - earlier) / earlier` | Applicable M5.4 JSON; cumulative `candidate_pairs` |

No additional metrics are introduced by this checkpoint.

## Resource observations — measured

The committed M5.4 report records peak RSS of approximately 7,228.86 MB for
M5.4.3 and 7,173.83 MB for M5.4.4. S2 and S3 were processed sequentially.
M5.5.1 performs no candidate-generation experiment.

## Threshold and interpretation boundaries

These tables describe measured threshold-250 cumulative experiments only.
They do not establish cumulative behavior at thresholds 5, 10, 25, 50, or
100. The tables normalize evidence; they do not select, rank, recommend, or
label any architecture as best, optimal, preferred, or final.
