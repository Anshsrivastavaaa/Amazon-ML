# M5.4.2 M4 + M5.2 Candidate Union

## Scope and method

This checkpoint measured the actual per-Source-1 candidate-set union:

```text
M4 country-aware rare-token blocking (frequency <= 250)
    union
M5.2 country-aware informative-address-token blocking (frequency <= 250)
```

S2 and S3 were evaluated independently on the fixed 20% Source-1 entity-level
validation split (`seed=42`, 441,365 entities). Candidate identities were
generated independently of ground truth and explicitly unioned per S1 entity.
Aggregate standalone recall values were not used to infer overlap.

The result artifact is
[`data/processed/part3_m54_m4_m52_union_results.json`](data/processed/part3_m54_m4_m52_union_results.json).

## Results

### S2

| Strategy | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 0.999993250 | 65.752 | 64.125 |
| M5.2 | 0.479146 | 0.514934 | 24,394,715 | 55.271 | 3 | 236 | 362 | 934 | 203,818 | 0.999989022 | 96.284 | 94.734 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 0.999982361 | 162.036 | 158.859 |

M5.2 added 24,196,703 candidate pairs to M4 and recovered 212,979 new
true pairs. This equals 0.288083 marginal pair recall, a cost of 113.611
added candidates per newly recovered pair, and 47.213% of the 451,100 pairs
missed by M4. It completed 111,236 additional entities.

### S3

| Strategy | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 0.999993557 | 65.567 | 64.297 |
| M5.2 | 0.446524 | 0.470369 | 24,260,236 | 54.966 | 3 | 236 | 362 | 923 | 203,335 | 0.999989601 | 100.166 | 98.797 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 0.999983237 | 165.733 | 163.094 |

M5.2 added 24,076,279 candidate pairs to M4 and recovered 218,433 new
true pairs. This equals 0.276689 marginal pair recall, a cost of 110.223
added candidates per newly recovered pair, and 44.819% of the 487,372 pairs
missed by M4. It completed 106,385 additional entities.

## Resource observations

S2 was processed before S3. No concurrent dataset experiment was run. Peak
process RSS was 6,437.30 MB. Disk free space remained approximately stable
(402.45 GB before and 402.47 GB after). The runner discarded intermediate
indexes and candidate maps between target sources.

## Interpretation and limits

The measured union substantially increases pair and complete-entity recall
over either standalone strategy, but also increases candidate volume. These
results establish measured complementarity for this fixed split and
threshold-250 configuration only. They do not select a final blocking
architecture and do not measure M5.3 marginal recovery. The final cumulative
architecture decision remains outside M5.4.2.
