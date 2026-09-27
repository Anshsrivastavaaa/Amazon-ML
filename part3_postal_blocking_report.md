# M5.3.2 — Postal-Only Blocking

## Protocol

- Validation: deterministic 20% Source 1 split, seed `42`
- Validation entities: `441,365`
- Target indexes: built without ground-truth labels
- Sources evaluated independently: S1→S2 and S1→S3
- Strategies: postal-only and country + postal
- Empty postal/country values were not universal keys
- No candidate cap or Cartesian product was used

Postal values are conservative candidate signals. They are not treated as
verified postal-code ground truth.

## Extraction behavior

| Source | Rows | Rows with postal signal | Multiple postal signals | Distinct signals | Signal occurrences |
|---|---:|---:|---:|---:|---:|
| S1 validation | 441,365 | 164,303 | 5,097 | — | — |
| S2 | 5,034,616 | 1,687,696 | 82,782 | 77,176 | 1,773,078 |
| S3 | 5,285,603 | 1,783,322 | 101,587 | 77,691 | 1,887,319 |

All 441,365 sampled S1 rows had a non-empty normalized address. Only 164,303
(37.23%) had at least one postal candidate.

## Results

### S1 → S2

| Strategy | Pair recall | Complete entity recall | Candidates | Mean | Median | P95 | P99 | Max | Zero S1 | Reduction | Runtime (s) | RSS (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Postal-only | 26.254% | 33.055% | 51,345,108 | 116.33 | 0 | 653 | 1,429 | 7,133 | 277,737 | 99.997689% | 11.39 | 4,622.93 |
| Country + postal | 26.254% | 33.055% | 38,878,639 | 88.09 | 0 | 502 | 925 | 3,527 | 277,846 | 99.998250% | 17.14 | 3,864.35 |

Block statistics:

- Postal-only: 77,176 blocks; maximum block 2,443; 4,361 blocks over 100;
  56 over 1,000.
- Country + postal: 88,731 blocks; maximum block 2,060; 4,217 blocks over
  100; 18 over 1,000.

### S1 → S3

| Strategy | Pair recall | Complete entity recall | Candidates | Mean | Median | P95 | P99 | Max | Zero S1 | Reduction | Runtime (s) | RSS (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Postal-only | 27.111% | 32.640% | 56,109,195 | 127.13 | 0 | 706 | 1,592 | 8,019 | 277,627 | 99.997595% | 8.48 | 5,437.72 |
| Country + postal | 27.111% | 32.640% | 42,873,102 | 97.14 | 0 | 560 | 1,031 | 3,995 | 277,722 | 99.998162% | 7.02 | 4,566.31 |

Block statistics:

- Postal-only: 77,691 blocks; maximum block 2,634; 4,572 blocks over 100;
  74 over 1,000.
- Country + postal: 89,218 blocks; maximum block 2,280; 4,448 blocks over
  100; 31 over 1,000.

## Recovery over approved passes

The artifact records pair-level recovery of true pairs missed by the approved
M4 country + Unicode rare-token threshold-250 pass and the M5.2 address-token
threshold-250 pass.

| Target | Postal strategy | M4 misses recovered | M5.2 misses recovered |
|---|---|---:|---:|
| S2 | Postal-only / country + postal | 119,088 | 112,104 |
| S3 | Postal-only / country + postal | 132,386 | 126,708 |

Postal-only and country + postal recovered the same true pairs in this
validation split. Country restriction therefore improved selectivity without
hurting measured postal recall.

## Conclusion

Postal blocking provides a materially different signal from name blocking, but
its candidate sets are substantially larger than M4 and M5.2. Country +
postal is preferable to postal-only for candidate cost in both target sources,
with identical measured recall here. Address-number blocking remains
unimplemented and will be evaluated separately in M5.3.3.
