# M5.3.4 — Postal and Address-Number Combination Blocking

## Protocol and semantics

- Validation: deterministic 20% Source 1 split, seed `42`
- Validation entities: `441,365`
- Sources evaluated independently: S1→S2 and S1→S3
- Target indexes were built without ground-truth labels
- Postal values and number values were unioned within each signal family
- Postal+number and country+postal+number used intersection across families
- Empty country, postal, and number values were never used as keys
- No Cartesian product or arbitrary candidate cap was used
- Number-frequency thresholds: `5`, `10`, `25`, `50`, `100`, `250`
- Country+postal was reused from the committed M5.3.4.2 artifact
- Country+number was reused from the committed M5.3.3 artifact
- Postal+number was reused from the committed M5.3.4.3 artifact
- The country+postal+number run was performed in M5.3.4.4

The consolidated artifact is
[`part3_signal_combination_results.json`](./data/processed/part3_signal_combination_results.json).

## Extraction and ambiguity

| Source | Rows | With postal | Multiple postal | With number | Multiple number |
|---|---:|---:|---:|---:|---:|
| S1 validation | 441,365 | 164,303 | 5,097 | 420,345 | 131,426 |
| S2 | 5,034,616 | 1,687,696 | 82,782 | 4,497,031 | 1,393,781 |
| S3 | 5,285,603 | 1,783,322 | 101,587 | 4,724,818 | 1,607,354 |

Postal extraction was available for 37.23% of validation rows; number
extraction was available for 95.24%. Multiple postal values occurred in
1.15% of validation rows, while multiple number values occurred in 29.77%.
The implementation therefore unions multiple values within each family.
Numbers and postal values are candidate signals only, not verified identifiers.

## S1 → S2

| Strategy | Threshold | Pair recall | Complete entity recall | Candidate pairs | Mean | Median | P95 | P99 | Max | Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Country + postal | — | 26.2537% | 33.0550% | 38,878,639 | 88.087 | 0 | 502 | 925 | 3,527 | 0.999982504 |
| Country + number | 5 | 0.9773% | 13.8310% | 17,401 | 0.039 | 0 | 0 | 2 | 8 | 1.000000 |
| Country + number | 10 | 1.7774% | 14.4266% | 52,167 | 0.118 | 0 | 0 | 5 | 16 | 1.000000 |
| Country + number | 25 | 3.4679% | 15.7006% | 217,545 | 0.493 | 0 | 0 | 17 | 51 | 1.000000 |
| Country + number | 50 | 5.6416% | 17.3439% | 690,588 | 1.565 | 0 | 11 | 41 | 98 | 1.000000 |
| Country + number | 100 | 9.4362% | 20.2239% | 2,296,959 | 5.204 | 0 | 49 | 86 | 225 | 0.999999 |
| Country + number | 250 | 17.2131% | 26.1659% | 9,306,502 | 21.086 | 0 | 151 | 215 | 463 | 0.999996 |
| Postal + number | 5 | 0.8292% | 13.6937% | 15,750 | 0.036 | 0 | 0 | 1 | 5 | 1.000000 |
| Postal + number | 10 | 1.5367% | 14.2179% | 48,604 | 0.110 | 0 | 0 | 5 | 13 | 1.000000 |
| Postal + number | 25 | 3.0544% | 15.3508% | 207,367 | 0.470 | 0 | 0 | 17 | 44 | 1.000000 |
| Postal + number | 50 | 5.0211% | 16.8294% | 662,588 | 1.501 | 0 | 10 | 40 | 115 | 1.000000 |
| Postal + number | 100 | 8.5177% | 19.4685% | 2,244,573 | 5.086 | 0 | 49 | 85 | 183 | 0.999999 |
| Postal + number | 250 | 15.7594% | 24.9857% | 9,604,847 | 21.762 | 0 | 157 | 221 | 933 | 0.999996 |
| Country + postal + number | 5 | 0.8292% | 13.6937% | 15,449 | 0.035 | 0 | 0 | 1 | 5 | 1.000000 |
| Country + postal + number | 10 | 1.5367% | 14.2179% | 47,615 | 0.108 | 0 | 0 | 5 | 13 | 1.000000 |
| Country + postal + number | 25 | 3.0544% | 15.3508% | 201,559 | 0.457 | 0 | 0 | 17 | 44 | 1.000000 |
| Country + postal + number | 50 | 5.0211% | 16.8294% | 636,140 | 1.441 | 0 | 9 | 39 | 88 | 1.000000 |
| Country + postal + number | 100 | 8.5177% | 19.4685% | 2,093,977 | 4.744 | 0 | 46 | 81 | 179 | 0.999999 |
| Country + postal + number | 250 | 15.7594% | 24.9857% | 8,465,910 | 19.181 | 0 | 141 | 202 | 428 | 0.999996 |

## S1 → S3

| Strategy | Threshold | Pair recall | Complete entity recall | Candidate pairs | Mean | Median | P95 | P99 | Max | Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Country + postal | — | 27.1108% | 32.6397% | 42,873,102 | 97.138 | 0 | 560 | 1,031 | 3,995 | 0.999981622 |
| Country + number | 5 | 0.9807% | 12.8678% | 17,218 | 0.039 | 0 | 0 | 2 | 9 | 1.000000 |
| Country + number | 10 | 1.7617% | 13.4564% | 51,010 | 0.116 | 0 | 0 | 5 | 18 | 1.000000 |
| Country + number | 25 | 3.4739% | 14.7250% | 213,201 | 0.483 | 0 | 0 | 17 | 41 | 1.000000 |
| Country + number | 50 | 5.5604% | 16.3173% | 657,970 | 1.491 | 0 | 10 | 40 | 90 | 1.000000 |
| Country + number | 100 | 9.3908% | 19.2238% | 2,220,037 | 5.030 | 0 | 48 | 86 | 204 | 0.999999 |
| Country + number | 250 | 17.0668% | 25.0885% | 9,059,948 | 20.527 | 0 | 150 | 215 | 460 | 0.999996 |
| Postal + number | 5 | 0.8274% | 12.7371% | 15,337 | 0.035 | 0 | 0 | 1 | 5 | 1.000000 |
| Postal + number | 10 | 1.5198% | 13.2550% | 47,321 | 0.107 | 0 | 0 | 5 | 15 | 1.000000 |
| Postal + number | 25 | 3.0714% | 14.3915% | 203,227 | 0.460 | 0 | 0 | 17 | 41 | 1.000000 |
| Postal + number | 50 | 4.9667% | 15.8307% | 633,087 | 1.434 | 0 | 8 | 40 | 90 | 1.000000 |
| Postal + number | 100 | 8.4833% | 18.4836% | 2,170,860 | 4.919 | 0 | 48 | 86 | 182 | 0.999999 |
| Postal + number | 250 | 15.6392% | 23.9287% | 9,320,584 | 21.118 | 0 | 158 | 221 | 964 | 0.999996 |
| Country + postal + number | 5 | 0.8274% | 12.7371% | 15,103 | 0.034 | 0 | 0 | 1 | 5 | 1.000000 |
| Country + postal + number | 10 | 1.5198% | 13.2550% | 46,354 | 0.105 | 0 | 0 | 5 | 15 | 1.000000 |
| Country + postal + number | 25 | 3.0714% | 14.3915% | 197,710 | 0.448 | 0 | 0 | 17 | 41 | 1.000000 |
| Country + postal + number | 50 | 4.9667% | 15.8307% | 609,202 | 1.380 | 0 | 8 | 39 | 90 | 1.000000 |
| Country + postal + number | 100 | 8.4833% | 18.4836% | 2,031,888 | 4.604 | 0 | 45 | 82 | 180 | 0.999999 |
| Country + postal + number | 250 | 15.6392% | 23.9287% | 8,276,302 | 18.752 | 0 | 140 | 203 | 436 | 0.999996 |

## Runtime and block distributions

The M5.3.4.4 country+postal+number run was executed once, serially, using
Python 3.11.9:

| Measure | Value |
|---|---:|
| Wall-clock time | 763.36 s |
| CPU time | 750.36 s |
| Peak RSS | 3,690.40 MB |
| RSS sampling interval | 0.25 s |

The artifact records indexed block counts, maximum block sizes, and oversized
block counts for both signal families at every threshold. No candidate cap was
used. Recovery overlap with M4 and M5.2 was not measured because the
evaluation does not retain the approved passes' per-pair candidate identities.

## Interpretation and limitations

- Country+postal has much higher standalone recall than combinations involving
  number, but also much larger candidate sets.
- At equal thresholds, country+postal+number has the same measured recall as
  postal+number and fewer candidates.
- Country restriction further reduces postal+number candidate volume without
  changing measured recall in this split.
- Number signals are highly available but ambiguous and frequently multiple.
- Postal signals are less available and also multi-valued for some rows.
- Aggregate recall does not establish M4-missed or M5.2-missed recovery.
- No final blocking strategy is selected by this checkpoint.
- M5.4 name+address integration is not started.
