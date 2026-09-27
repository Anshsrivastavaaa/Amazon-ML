# M5.5.3 Threshold-5 Cumulative Sensitivity Result

## Scope

This checkpoint measures threshold 5 only. Thresholds 25, 100, 250, 10, and
50 were not executed. The authoritative threshold-250 cumulative rows were
reused from the committed M5.4.3/M5.4.4 artifacts; threshold 250 was not
regenerated.

Protocol:

- validation fraction: 20%;
- seed: 42;
- validation Source-1 entities: 441,365;
- split unit: Source-1 entity;
- targets processed sequentially: S2, then S3;
- Python 3.11;
- ground truth used only after candidate construction;
- actual per-S1 candidate identities;
- no candidate cap or Cartesian product.

The result artifact is
[part3_m553_threshold5_results.json](data/processed/part3_m553_threshold5_results.json).
The runner was parameterized so M4 and M5.2 remain fixed at approved
frequency 250 while only M5.3.3/M5.3.4 use the selected sensitivity
threshold.

## Preflight and resource outcome

Existing standalone threshold-5 evidence predicted small incremental signal
volumes:

| Target | Country+number candidates | Country+postal+number candidates |
|---|---:|---:|
| S2 | 17,401 | 15,449 |
| S3 | 17,218 | 15,103 |

The cumulative M4 ∪ M5.2 baseline remained the dominant candidate set at
39,196,644 pairs for S2 and 39,106,086 for S3.

Measured run outcome:

- peak RSS: `7,621.754 MB`;
- post-run free disk snapshot: `431.583 GB`;
- S2 and S3 completed sequentially;
- no process was left running.

Peak RSS exceeded the prior M5.4 reference of approximately 7.2 GB. This is
recorded as a resource concern; semantics were not changed and no candidate
cap was introduced.

## S2 cumulative results — measured

| Stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero S1 | Reduction | Wall s | CPU s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 0.999993250 | 61.103 | 60.234 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 0.999982361 | 158.469 | 156.031 |
| M4 ∪ M5.2 ∪ M5.3.3(5) | 0.680542 | 0.681991 | 39,207,683 | 88.833 | 51 | 296 | 434 | 1,115 | 110,009 | 0.999982356 | 316.077 | 310.656 |
| Full threshold-5 union | 0.680542 | 0.681991 | 39,207,683 | 88.833 | 51 | 296 | 434 | 1,115 | 110,009 | 0.999982356 | 437.041 | 429.969 |

## S3 cumulative results — measured

| Stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero S1 | Reduction | Wall s | CPU s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 0.999993557 | 65.772 | 65.156 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 0.999983237 | 164.969 | 163.313 |
| M4 ∪ M5.2 ∪ M5.3.3(5) | 0.662014 | 0.654098 | 39,116,510 | 88.626 | 51 | 296 | 434 | 1,115 | 110,504 | 0.999983233 | 325.248 | 321.250 |
| Full threshold-5 union | 0.662014 | 0.654098 | 39,116,510 | 88.626 | 51 | 296 | 434 | 1,115 | 110,504 | 0.999983233 | 453.385 | 447.656 |

## S2 marginal contributions — measured identities

| Addition | New pairs | New entities | Added candidates | Candidate cost | Previous misses recovered |
|---|---:|---:|---:|---:|---:|
| M5.3.3(5) after M4 ∪ M5.2 | 1,946 | 1,063 | 11,039 | 5.673 | 0.817% |
| M5.3.4(5) after prior union | 0 | 0 | 0 | None | 0.000% |

## S3 marginal contributions — measured identities

| Addition | New pairs | New entities | Added candidates | Candidate cost | Previous misses recovered |
|---|---:|---:|---:|---:|---:|
| M5.3.3(5) after M4 ∪ M5.2 | 2,115 | 1,096 | 10,424 | 4.929 | 0.786% |
| M5.3.4(5) after prior union | 0 | 0 | 0 | None | 0.000% |

Marginal candidate cost is:

`marginal candidate pairs / newly recovered true pairs`

and is `None` when no new true pair is recovered.

## Candidate growth — derived from measured identities

| Target | Addition | Earlier pairs | Later pairs | Growth |
|---|---|---:|---:|---:|
| S2 | M5.3.3(5) | 39,196,644 | 39,207,683 | 0.0002816 |
| S2 | M5.3.4(5) | 39,207,683 | 39,207,683 | 0.0000000 |
| S3 | M5.3.3(5) | 39,106,086 | 39,116,510 | 0.0002665 |
| S3 | M5.3.4(5) | 39,116,510 | 39,116,510 | 0.0000000 |

Formula:

`(later candidate pairs - earlier candidate pairs) / earlier candidate pairs`

## Provenance and validation boundaries

- M4 and M5.2 cumulative identities match the committed M5.4.2/M5.4.3
  evidence.
- M5.3.3(5) uses the approved country+number semantics.
- M5.3.4(5) uses the approved country+postal+number intersection semantics.
- Empty signal values remain excluded.
- Multiple signal values retain union semantics within each family.
- Threshold 250 was reused, not regenerated.
- Standalone threshold rows were used only for preflight estimates; they were
  not treated as cumulative recall.

This report does not extrapolate threshold-5 results to any other threshold,
does not rank thresholds, and does not select an architecture.
