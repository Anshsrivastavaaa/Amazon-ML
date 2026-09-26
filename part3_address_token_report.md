# Part 3 — M5.2 Country-Aware Address-Token Blocking

## Scope

M5.2 evaluates only country-aware informative address-token blocking. It does
not implement postal blocking, address-number blocking, name+address
combinations, approximate retrieval, or model code.

Implementation:
[`src/part3_address_blocking.py`](./src/part3_address_blocking.py)

Artifact:
[`data/processed/part3_address_token_results.json`](./data/processed/part3_address_token_results.json)

## Method

- Same deterministic 20% Source 1 validation split as M3/M4.
- Seed: `42`.
- Validation entities: `441,365`.
- S1→S2 and S1→S3 evaluated independently.
- Address representation: `informative_address_tokens()` from
  [`src/part3_address.py`](./src/part3_address.py).
- Empty countries and empty/informative-token values do not create universal
  keys.
- No candidate cap was applied.
- Thresholds measured: `5`, `10`, `25`, `50`, `100`, `250` target records per
  country-token block.
- Postal and address-number signals were not used.

Address numbers and postal-like values remain candidate signals only and are
reserved for M5.3.

## S1→S2 results

M4 comparison is the strongest approved M4 pass:
country + Unicode name token, frequency ≤250: `38.983%` pair recall and
`14,999,941` candidates.

| Threshold | Pair recall | Complete entity recall | Candidates | Avg | Median | P95 | P99 | Max | Zero | Reduction | Runtime (s) | RSS (MB) | M4-missed recovery |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 10.838% | 22.089% | 157,525 | 0.36 | 0 | 3 | 5 | 12 | 385,910 | 99.999993% | 7.2 | 2,086 | 10.63% |
| 10 | 15.589% | 25.622% | 357,705 | 0.81 | 0 | 6 | 10 | 26 | 364,341 | 99.999985% | 8.1 | 2,261 | 15.24% |
| 25 | 22.608% | 31.150% | 1,116,971 | 2.53 | 0 | 17 | 25 | 79 | 330,284 | 99.999951% | 53.3 | 2,399 | 22.16% |
| 50 | 28.738% | 36.036% | 2,725,214 | 6.17 | 0 | 38 | 54 | 184 | 299,874 | 99.999893% | 52.1 | 2,513 | 28.20% |
| 100 | 36.033% | 41.883% | 6,897,787 | 15.63 | 0 | 85 | 123 | 343 | 263,199 | 99.999729% | 59.4 | 2,858 | 35.39% |
| 250 | 47.915% | 51.493% | 24,394,715 | 55.27 | 3 | 236 | 362 | 934 | 203,818 | 99.999680% | 65.7 | 3,797 | 47.21% |

Increment over strongest M4:

- Threshold 100: `-2.950` percentage points and `-8,102,154` candidates.
- Threshold 250: `+8.932` percentage points and `+9,394,774` candidates.

## S1→S3 results

M4 comparison is the strongest approved M4 pass:
country + Unicode name token, frequency ≤250: `38.265%` pair recall and
`15,029,807` candidates.

| Threshold | Pair recall | Complete entity recall | Candidates | Avg | Median | P95 | P99 | Max | Zero | Reduction | Runtime (s) | RSS (MB) | M4-missed recovery |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 9.996% | 20.069% | 160,125 | 0.36 | 0 | 3 | 5 | 13 | 384,639 | 99.999993% | 45.3 | 2,540 | 10.00% |
| 10 | 14.356% | 23.256% | 365,291 | 0.83 | 0 | 6 | 10 | 31 | 362,712 | 99.999985% | 49.3 | 2,427 | 14.35% |
| 25 | 20.897% | 28.243% | 1,143,091 | 2.59 | 0 | 18 | 25 | 81 | 328,326 | 99.999951% | 51.1 | 2,504 | 21.01% |
| 50 | 26.713% | 32.784% | 2,785,159 | 6.31 | 0 | 39 | 55 | 156 | 297,429 | 99.999900% | 8.3 | 2,643 | 26.87% |
| 100 | 33.595% | 38.179% | 7,019,717 | 15.90 | 0 | 85 | 125 | 356 | 260,958 | 99.999749% | 92.4 | 2,882 | 33.77% |
| 250 | 44.652% | 47.037% | 24,260,236 | 54.97 | 3 | 236 | 362 | 923 | 203,335 | 99.999870% | 61.6 | 4,171 | 44.82% |

Increment over strongest M4:

- Threshold 100: `-4.670` percentage points and `-8,010,090` candidates.
- Threshold 250: `+6.388` percentage points and `+9,230,429` candidates.

## Frequency and oversized-block behavior

| Target | Threshold | Distinct tokens | Indexed country-token blocks | P95 block | P99 block | Max block | Blocks >100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| S2 | 5 | 535,737 | 411,091 | 5 | 5 | 5 | 0 |
| S2 | 25 | 535,737 | 505,769 | 13 | 21 | 25 | 0 |
| S2 | 100 | 535,737 | 535,648 | 24 | 64 | 100 | 0 |
| S2 | 250 | 535,737 | 544,966 | 31 | 118 | 250 | 7,122 |
| S3 | 5 | 507,515 | 388,178 | 5 | 5 | 5 | 0 |
| S3 | 25 | 507,515 | 479,581 | 13 | 21 | 25 | 0 |
| S3 | 100 | 507,515 | 508,714 | 24 | 64 | 100 | 0 |
| S3 | 250 | 507,515 | 517,580 | 31 | 118 | 250 | 6,732 |

No block exceeded 1,000 records in either source at the tested thresholds.
Threshold 250 introduces thousands of blocks larger than 100 and produces
substantial candidate growth.

## Missing-address behavior

The validation sample reported zero Source 1 entities with an empty raw
address in both target evaluations. This does not imply that all records in
the full corpus have usable addresses; it only describes this validation
split. Empty address/token values were never indexed as universal keys, so
records without informative address tokens receive no address-token
candidates from this pass.

## Conclusion

Address-token blocking is complementary to M4, but it is not a replacement for
the strongest M4 pass at thresholds ≤100. Threshold 250 recovers additional
M4 misses and raises recall to `47.915%` for S2 and `44.652%` for S3, but at
approximately `55` candidates per S1 and significant memory/candidate growth.

M5.2 does not select a final threshold. The measured tradeoff should be
combined with the later postal/address-number experiments in M5.3 before any
M5.4 name+address composition is considered.
