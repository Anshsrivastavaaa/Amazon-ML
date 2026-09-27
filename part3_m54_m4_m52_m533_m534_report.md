# M5.4.4 M5.3.4 Incremental Candidate Union

## Scope and semantics

This checkpoint measured the actual cumulative candidate set:

```text
M4
  union M5.2
  union M5.3.3 country+number
  union M5.3.4 country+postal+number
```

All strategies used threshold 250. M5.3.4 used the approved country-aware
postal/number intersection semantics, with union within each signal family,
empty values excluded from keys, and no Cartesian product. Candidate identities
were generated independently of ground truth and explicitly unioned per
Source-1 entity.

Validation used the fixed 20% Source-1 entity-level split (`seed=42`,
441,365 entities). S2 and S3 were processed sequentially.

Artifact:
[`data/processed/part3_m54_m4_m52_m533_m534_union_results.json`](data/processed/part3_m54_m4_m52_m533_m534_union_results.json)

## S2 results

| Strategy | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 0.999993250 | 65.310 | 64.063 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 0.999982361 | 163.062 | 159.734 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 319.973 | 312.203 |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 443.278 | 432.672 |

### S2 M5.3.4 marginal contribution

- Newly recovered true pairs: **0**
- Newly complete entities: **0**
- Candidate-pair increase: **0**
- Marginal pair-recall gain: **0**
- Marginal candidate cost: **None** because no new pairs were recovered
- Previously missed cumulative pairs: **197,046**
- Previously missed pairs recovered: **0%**

The M5.3.4 candidate set produced no additional candidates beyond the
already-present cumulative set for S2.

## S3 results

| Strategy | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 0.999993557 | 66.603 | 65.406 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 0.999983237 | 167.819 | 164.562 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 339.701 | 329.406 |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 472.372 | 459.656 |

### S3 M5.3.4 marginal contribution

- Newly recovered true pairs: **0**
- Newly complete entities: **0**
- Candidate-pair increase: **0**
- Marginal pair-recall gain: **0**
- Marginal candidate cost: **None** because no new pairs were recovered
- Previously missed cumulative pairs: **224,883**
- Previously missed pairs recovered: **0%**

The M5.3.4 candidate set produced no additional candidates beyond the
already-present cumulative set for S3.

## Extraction and resource observations

For S2, M5.3.4 validation availability was 102,883 entities with postal
signals and 105,825 with number signals. For S3, availability was 98,499
with postal signals and 102,073 with number signals.

Peak RSS was **7,173.83 MB**. Disk free space changed from 402.27 GB to
402.26 GB. No concurrent dataset experiment ran, and intermediate structures
were discarded between targets.

No lower-threshold sensitivity sweep was run. These results are measured
threshold-250 evidence only and do not select a final blocking architecture.
