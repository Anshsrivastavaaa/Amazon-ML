# M5.3.3 — Address-Number Blocking

## Protocol

- Validation: deterministic 20% Source 1 split, seed `42`
- Validation entities: `441,365`
- Split unit: Source 1 entity
- Target indexes: built without ground-truth labels
- Sources evaluated independently: S1→S2 and S1→S3
- Strategies: number-only and country + number
- Frequency thresholds: `5`, `10`, `25`, `50`, `100`, `250`
- Empty number and empty country values were not universal keys
- Multiple extracted numbers were queried as a set union
- No candidate cap or Cartesian product was used

The implementation is in
[`src/part3_signal_evaluation.py`](./src/part3_signal_evaluation.py), using
the reusable indexes in
[`src/part3_signal_blocking.py`](./src/part3_signal_blocking.py). The complete
experiment artifact is
[`part3_number_results.json`](./data/processed/part3_number_results.json).

## Extraction behavior and ambiguity

| Source | Rows | Rows with number | Multiple-number rows | Distinct signals | Signal occurrences |
|---|---:|---:|---:|---:|---:|
| S1 validation | 441,365 | 420,345 | 131,426 | — | — |
| S2 | 5,034,616 | 4,497,031 | 1,393,781 | 96,980 | 6,640,377 |
| S3 | 5,285,603 | 4,724,818 | 1,607,354 | 97,664 | 7,014,731 |

All sampled S1 rows had a non-empty normalized address. Number extraction was
available for 95.24% of validation rows. Multiple numbers occurred in 29.77%
of validation rows, so a row-level single-number key would be incomplete.
Numbers are candidate signals only: common values can represent apartment,
street, postal, or other address components and are not verified identifiers.

## Results

The reduction ratio is relative to the full validation-S1 × target-source
Cartesian pair count. Values near `1.0` are displayed at six decimal places;
the underlying candidate counts are the more useful comparison at this scale.

### S1 → S2

| Threshold | Strategy | Pair recall | Complete entity recall | Candidates | Mean | Median | P95 | P99 | Max | Zero S1 | Reduction | Runtime (s) | RSS (MB) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | Number-only | 0.9773% | 13.8310% | 18,205 | 0.041 | 0 | 0 | 2 | 9 | 435,091 | 1.000000 | 1.312 | 3,636.15 |
| 5 | Country + number | 0.9773% | 13.8310% | 17,401 | 0.039 | 0 | 0 | 2 | 8 | 435,199 | 1.000000 | 1.277 | 3,636.15 |
| 10 | Number-only | 1.7774% | 14.4266% | 54,936 | 0.124 | 0 | 0 | 6 | 16 | 430,450 | 1.000000 | 1.333 | 3,636.15 |
| 10 | Country + number | 1.7774% | 14.4266% | 52,167 | 0.118 | 0 | 0 | 5 | 16 | 430,590 | 1.000000 | 1.340 | 3,636.15 |
| 25 | Number-only | 3.4679% | 15.7006% | 231,094 | 0.524 | 0 | 0 | 18 | 51 | 420,317 | 1.000000 | 0.655 | 3,636.15 |
| 25 | Country + number | 3.4679% | 15.7006% | 217,545 | 0.493 | 0 | 0 | 17 | 51 | 420,518 | 1.000000 | 0.729 | 3,636.15 |
| 50 | Number-only | 5.6416% | 17.3439% | 739,688 | 1.676 | 0 | 12 | 42 | 118 | 407,050 | 1.000000 | 0.749 | 3,636.15 |
| 50 | Country + number | 5.6416% | 17.3439% | 690,588 | 1.565 | 0 | 11 | 41 | 98 | 407,370 | 1.000000 | 0.828 | 3,636.15 |
| 100 | Number-only | 9.4362% | 20.2239% | 2,502,573 | 5.670 | 0 | 54 | 90 | 225 | 383,664 | 0.999999 | 1.043 | 3,636.15 |
| 100 | Country + number | 9.4362% | 20.2239% | 2,296,959 | 5.204 | 0 | 49 | 86 | 225 | 384,041 | 0.999999 | 1.119 | 3,636.15 |
| 250 | Number-only | 17.2131% | 26.1659% | 10,624,896 | 24.073 | 0 | 170 | 235 | 958 | 336,379 | 0.999995 | 2.702 | 3,636.15 |
| 250 | Country + number | 17.2131% | 26.1659% | 9,306,502 | 21.086 | 0 | 151 | 215 | 463 | 336,778 | 0.999996 | 2.074 | 3,636.15 |

### S1 → S3

| Threshold | Strategy | Pair recall | Complete entity recall | Candidates | Mean | Median | P95 | P99 | Max | Zero S1 | Reduction | Runtime (s) | RSS (MB) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | Number-only | 0.9807% | 12.8678% | 17,859 | 0.040 | 0 | 0 | 2 | 9 | 435,269 | 1.000000 | 0.595 | 3,636.15 |
| 5 | Country + number | 0.9807% | 12.8678% | 17,218 | 0.039 | 0 | 0 | 2 | 9 | 435,318 | 1.000000 | 0.705 | 3,636.15 |
| 10 | Number-only | 1.7617% | 13.4564% | 53,655 | 0.122 | 0 | 0 | 6 | 19 | 430,796 | 1.000000 | 0.579 | 3,636.15 |
| 10 | Country + number | 1.7617% | 13.4564% | 51,010 | 0.116 | 0 | 0 | 5 | 18 | 430,862 | 1.000000 | 0.665 | 3,636.15 |
| 25 | Number-only | 3.4739% | 14.7250% | 226,073 | 0.512 | 0 | 0 | 18 | 45 | 420,961 | 1.000000 | 1.382 | 3,636.15 |
| 25 | Country + number | 3.4739% | 14.7250% | 213,201 | 0.483 | 0 | 0 | 17 | 41 | 421,051 | 1.000000 | 1.442 | 3,636.15 |
| 50 | Number-only | 5.5604% | 16.3173% | 701,391 | 1.589 | 0 | 11 | 42 | 99 | 408,515 | 1.000000 | 1.394 | 3,636.15 |
| 50 | Country + number | 5.5604% | 16.3173% | 657,970 | 1.491 | 0 | 0 | 10 | 40 | 408,628 | 1.000000 | 1.611 | 3,636.15 |
| 100 | Number-only | 9.3908% | 19.2238% | 2,413,298 | 5.468 | 0 | 52 | 91 | 232 | 385,832 | 0.999999 | 1.869 | 3,636.15 |
| 100 | Country + number | 9.3908% | 19.2238% | 2,220,037 | 5.030 | 0 | 48 | 86 | 204 | 385,965 | 0.999999 | 1.860 | 3,636.15 |
| 250 | Number-only | 17.0668% | 25.0885% | 10,295,428 | 23.326 | 0 | 169 | 234 | 996 | 339,962 | 0.999996 | 3.062 | 3,636.15 |
| 250 | Country + number | 17.0668% | 25.0885% | 9,059,948 | 20.527 | 0 | 150 | 215 | 460 | 340,104 | 0.999996 | 1.975 | 3,636.15 |

## Block-size distribution

The artifact records, for each target, strategy, and threshold, the indexed
block count, maximum block size, and counts over 100, 1,000, and 10,000
members. No candidate cap was applied. The maximum observed per-S1 candidate set was 958 for S2 number-only at
threshold 250 and 996 for S3 number-only at threshold 250. Country restriction
reduced those maxima to 463 and 460 respectively. The largest indexed block
was 250 members because each threshold excludes signals above that frequency.
No retained block exceeded 10,000 members at the evaluated thresholds.

## Runtime and resource behavior

The single serial Python 3.11.9 experiment completed in:

| Measure | Value |
|---|---:|
| Wall-clock time | 452.92 s |
| CPU time | 444.72 s |
| Peak RSS | 3,636.15 MB |
| RSS sampling interval | 0.25 s |

The per-run runtime and RSS fields remain in the artifact. RSS is a process
sample rather than a hard allocator maximum.

## M4 and M5.2 recovery

The M5.3.3 implementation measures pair recall and complete-entity recall
against the ground truth, but it does not retain per-pair candidate sets or
the approved M4/M5.2 candidate sets. Consequently, exact M4-missed and
M5.2-missed recovery overlap cannot be computed from this artifact without
rerunning those passes together and retaining their candidate identities.
Those recovery values are intentionally reported as **not measured**, rather
than inferred from aggregate recall.

For context only, the prior M5.3.2 postal artifact did retain recovery
comparisons and reported 119,088/112,104 recovered S2 pairs and
132,386/126,708 recovered S3 pairs for M4/M5.2 misses respectively. Those
postal values are not number-blocking results and are not combined with this
checkpoint.

## Limitations

- Extracted numbers are ambiguous address components and are not verified
  identifiers.
- Frequency is measured across each target source, not conditioned on country.
- Country-aware lookup excludes rows with empty country; number-only lookup
  does not.
- The split and ground truth are unchanged from earlier checkpoints, but
  validation remains a sampled Source 1 split.
- M4/M5.2 recovery overlap is not available in this isolated artifact.
- No final number threshold or strategy is selected here.
- Number blocking is not combined with postal, M5.2, or M4 in this report.
