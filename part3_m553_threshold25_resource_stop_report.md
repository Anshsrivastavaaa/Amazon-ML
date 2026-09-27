# M5.5.3 Threshold-25 Resource-Stop Evidence

## Status

The threshold-25 experiment **completed and its measured result was
captured**. The M5.5.3 checkpoint was then stopped before any further
sensitivity execution because peak RSS exceeded the observed resource
reference. This is a resource-limited checkpoint, not an experiment failure.

No threshold 100, 50, or 10 run was executed. Threshold 25 was not rerun.
M5.5.4 was not started. The preserved result artifact is
[part3_m553_threshold25_results.json](data/processed/part3_m553_threshold25_results.json).

## Protocol

- threshold: 25 for M5.3.3 and M5.3.4;
- M4 and M5.2 baseline reused at approved threshold 250;
- validation fraction: 20%;
- seed: 42;
- validation Source-1 entities: 441,365;
- Source-1 entity-level split;
- S2 and S3 processed sequentially;
- actual per-S1 candidate identity unions;
- no candidate cap or Cartesian product;
- ground truth used only after candidate construction.

The threshold-250 cumulative rows were not regenerated.

## S2 cumulative results — measured

| Stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero S1 | Wall s | CPU s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 66.445 | 65.313 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 51 | 296 | 434 | 1,115 | 111,444 | 188.533 | 185.703 |
| M4 ∪ M5.2 ∪ M5.3.3(25) | 0.688069 | 0.688344 | 39,380,227 | 89.224 | 51 | 297 | 435 | 1,115 | 106,236 | 392.727 | 386.859 |
| Full threshold-25 union | 0.688069 | 0.688344 | 39,380,227 | 89.224 | 51 | 297 | 435 | 1,115 | 106,236 | 512.613 | 504.922 |

## S3 cumulative results — measured

| Stage | Pair recall | Complete entity recall | Candidate pairs | Avg/S1 | Median | P95 | P99 | Max | Zero S1 | Wall s | CPU s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 70.877 | 70.031 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 51 | 296 | 434 | 1,115 | 111,968 | 198.730 | 195.953 |
| M4 ∪ M5.2 ∪ M5.3.3(25) | 0.669517 | 0.660533 | 39,284,812 | 89.008 | 51 | 296 | 434 | 1,115 | 106,782 | 410.563 | 404.531 |
| Full threshold-25 union | 0.669517 | 0.660533 | 39,284,812 | 89.008 | 51 | 296 | 434 | 1,115 | 106,782 | 537.889 | 529.500 |

## Marginal recovery — measured candidate identities

| Target | Addition | New pairs | New complete entities | Added candidates | Candidate cost | Previous misses recovered |
|---|---|---:|---:|---:|---:|---:|
| S2 | M5.3.3(25) after M4 ∪ M5.2 | 7,511 | 3,867 | 183,583 | 24.442 | 3.154% |
| S2 | M5.3.4(25) after prior union | 0 | 0 | 0 | None | 0.000% |
| S3 | M5.3.3(25) after M4 ∪ M5.2 | 8,038 | 3,936 | 178,726 | 22.235 | 2.989% |
| S3 | M5.3.4(25) after prior union | 0 | 0 | 0 | None | 0.000% |

Marginal candidate cost is:

`added candidate pairs / newly recovered true pairs`

and is `None` when no newly recovered true pair exists.

## Candidate-pair growth — derived

Formula:

`(later candidate pairs - earlier candidate pairs) / earlier candidate pairs`

| Target | Addition | Earlier pairs | Later pairs | Added pairs | Growth |
|---|---|---:|---:|---:|---:|
| S2 | M5.3.3(25) | 39,196,644 | 39,380,227 | 183,583 | 0.004683 |
| S2 | M5.3.4(25) | 39,380,227 | 39,380,227 | 0 | 0.000000 |
| S3 | M5.3.3(25) | 39,106,086 | 39,284,812 | 178,726 | 0.004570 |
| S3 | M5.3.4(25) | 39,284,812 | 39,284,812 | 0 | 0.000000 |

## Runtime, RSS, and disk — measured

- S2 full run wall time: `512.613 s`
- S2 full run CPU time: `504.922 s`
- S3 full run wall time: `537.889 s`
- S3 full run CPU time: `529.500 s`
- Peak RSS: `8,438.969 MB`
- Post-run free disk snapshot: approximately `431.780 GB`
- No Python process remained active after completion.

Resource history:

| Checkpoint | Peak RSS |
|---|---:|
| M5.4 reference | ~7,228.855 MB |
| Threshold 5 | 7,621.754 MB |
| Threshold 25 | 8,438.969 MB |

## Explicit resource-stop reason

The experiment result was captured successfully, but the checkpoint stopped
before further sensitivity execution because threshold 25 reached
`8,438.969 MB` peak RSS, materially above the observed M5.4 reference and
above threshold 5. No semantics were changed to reduce memory usage, no
candidate cap was introduced, and no further threshold experiment was
attempted.

## Validation

- Artifact threshold: `25`.
- Validation split: `20%`, seed `42`, `441,365` Source-1 entities.
- S2 and S3 rows present.
- Five cumulative identity rows present per target.
- Cumulative candidate arithmetic validated.
- Marginal candidate-pair arithmetic validated.
- Marginal candidate-cost formulas validated.
- M5.3.4 zero-contribution result validated for both targets.
- M4 ∪ M5.2 candidate counts match the locked baseline.
- Threshold 250 was not regenerated.
- Python 3.11 validation completed.
- Focused tests: **13 passed**.
- Pylance syntax check: passed for [part3_m54_evaluation.py](src/part3_m54_evaluation.py).
- `git diff --check`: passed before this report-only change.

## Limitations

- Threshold 25 is a single measured cumulative point; no threshold 100, 50,
  or 10 result exists.
- The resource stop prevents completing the planned sensitivity sweep.
- RSS is a process-level peak measurement, not a general hardware limit.
- No architecture or threshold is selected, ranked, or recommended.
- Results remain specific to the approved validation split and semantics.
