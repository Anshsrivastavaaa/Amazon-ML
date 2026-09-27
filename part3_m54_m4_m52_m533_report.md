# M5.4.3 M4 + M5.2 + M5.3.3 Candidate Union

## Scope

This checkpoint measured the actual cumulative candidate set:

```text
M4 country-aware rare-token blocking, frequency <= 250
    union
M5.2 country-aware informative-address-token blocking, frequency <= 250
    union
M5.3.3 country-aware address-number blocking, frequency <= 250
```

Candidate identities were explicitly generated and unioned per Source-1
entity. Ground truth was used only for evaluation. The validation split is the
fixed 20% Source-1 entity-level split (`seed=42`, 441,365 entities).

Artifact:
[`data/processed/part3_m54_m4_m52_m533_union_results.json`](data/processed/part3_m54_m4_m52_m533_union_results.json)

## S2 results

| Strategy | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 0.999993250 | 63.461 | 62.578 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 0.999982361 | 159.529 | 156.703 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 78 | 328 | 458 | 1,115 | 82,780 | 0.999978375 | 317.322 | 309.906 |

### S2 marginal M5.3.3 contribution

- Newly recovered true pairs: **41,075**
- Newly complete entities: **21,119**
- Candidate-pair increase: **8,857,341**
- Marginal pair-recall gain: **0.055559**
- Marginal candidate cost: **215.638 added candidates per newly recovered pair**
- Previously missed M4∪M5.2 pairs: **238,121**
- Previously missed pairs recovered: **17.250%**

M5.3.3 extraction availability was 105,825 / 441,365 validation entities
with numbers. Its S2 threshold-250 country-aware index had 107,905 blocks,
maximum block size 247, and no blocks over 1,000.

## S3 results

| Strategy | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero-candidate S1 | Reduction ratio | Runtime (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 0.999993557 | 65.004 | 63.938 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 0.999983237 | 164.767 | 161.922 |
| M4 ∪ M5.2 ∪ M5.3.3 | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 77 | 327 | 457 | 1,115 | 83,737 | 0.999979542 | 326.819 | 319.375 |

### S3 marginal M5.3.3 contribution

- Newly recovered true pairs: **44,056**
- Newly complete entities: **21,547**
- Candidate-pair increase: **8,619,850**
- Marginal pair-recall gain: **0.055806**
- Marginal candidate cost: **195.657 added candidates per newly recovered pair**
- Previously missed M4∪M5.2 pairs: **268,939**
- Previously missed pairs recovered: **16.381%**

M5.3.3 extraction availability was 102,073 / 441,365 validation entities
with numbers. Its S3 threshold-250 country-aware index had 108,601 blocks,
maximum block size 246, and no blocks over 1,000.

## Resource observations and limitations

S2 was processed before S3, with no concurrent dataset experiment. Peak RSS
was 7,228.86 MB. Disk free space changed from 402.49 GB to 402.27 GB. The
runner discarded intermediate maps between target sources.

Only the approved threshold-250 M5.3.3 configuration was evaluated. Lower
threshold sensitivity analysis was not run. These results measure incremental
contribution from explicit candidate identities and do not select a final
blocking architecture.
