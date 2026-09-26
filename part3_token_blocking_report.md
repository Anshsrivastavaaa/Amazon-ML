# Part 3 — M4 Rare-Token and Multi-Token Blocking

## Scope

M4 evaluates name-token blocking only. It does not implement address,
postal-number, character-ngram, approximate retrieval, feature engineering, or
ML. Parts 1 and 2 and the M3 exact-name baseline are unchanged.

Implementation:
[`src/part3_token_blocking.py`](./src/part3_token_blocking.py)

Structured results:
[`data/processed/part3_token_results.json`](./data/processed/part3_token_results.json)

## Evaluation design

- Same deterministic 20% Source 1 validation split as M3.
- Seed: `42`.
- Validation entities: `441,365`.
- S1→S2 and S1→S3 evaluated independently.
- No candidate cap was applied.
- Target token frequencies were measured empirically.
- Frequency thresholds tested: `10`, `25`, `50`, `100`, `250`.
- Part 2 name representations tested:
  - `name_clean_unicode`
  - `name_nopunct`

Strategies:

1. Rare token: union of target records sharing any selected informative token.
2. Country + rare token: same pass keyed by `(country_clean, token)`.
3. Two-token intersection: intersection of the two least-frequent available
   target token blocks.
4. Sorted two-token signature: exact lookup on the sorted pair of the two
   least-frequent tokens.

The structured artifact contains all 80 runs: 2 target sources × 2
representations × 5 thresholds × 4 strategies.

## M3 baseline versus M4 rare-token blocking

The most useful M4 family was `country_rare_token_name_clean_unicode`. Country
constraining reduced candidate cost without reducing measured recall in this
validation set.

### S1→S2

| Strategy | Pair recall | Complete entity recall | Candidates | Avg/S1 | Median | P95 | P99 | Max | Zero candidates | Reduction | Runtime (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M3 compact baseline | 21.409% | 22.341% | 2,064,942 | 4.679 | 1 | 30 | 88 | 224 | 207,325 | 99.999907% | 49.55 |
| Country + token, freq ≤50 | 21.683% | 29.388% | 2,632,309 | 5.964 | 0 | 39 | 51 | 131 | 325,759 | 99.999882% | 7.56 |
| Country + token, freq ≤100 | 30.880% | 36.475% | 6,777,080 | 15.355 | 0 | 81 | 110 | 285 | 280,234 | 99.999695% | 17.29 |
| Country + token, freq ≤250 | 38.983% | 42.756% | 14,999,941 | 33.985 | 0 | 168 | 249 | 684 | 240,031 | 99.999325% | 20.24 |

Increment over M3:

- Threshold 50: `+0.274` percentage points, `+567,367` candidates.
- Threshold 100: `+9.471` percentage points, `+4,712,138` candidates.
- Threshold 250: `+17.574` percentage points, `+12,934,999` candidates.

### S1→S3

| Strategy | Pair recall | Complete entity recall | Candidates | Avg/S1 | Median | P95 | P99 | Max | Zero candidates | Reduction | Runtime (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M3 compact baseline | 22.187% | 21.442% | 2,279,905 | 5.166 | 1 | 31 | 88 | 235 | 195,698 | 99.999902% | 47.34 |
| Country + token, freq ≤50 | 21.007% | 27.817% | 2,556,435 | 5.792 | 0 | 39 | 50 | 134 | 328,638 | 99.999890% | 8.36 |
| Country + token, freq ≤100 | 30.141% | 34.805% | 6,750,492 | 15.295 | 0 | 81 | 110 | 281 | 282,726 | 99.999711% | 10.96 |
| Country + token, freq ≤250 | 38.265% | 41.058% | 15,029,807 | 34.053 | 0 | 168 | 249 | 724 | 242,191 | 99.999356% | 10.15 |

Increment over M3:

- Threshold 50: `-1.180` percentage points, `+276,530` candidates.
- Threshold 100: `+7.954` percentage points, `+4,470,587` candidates.
- Threshold 250: `+16.078` percentage points, `+12,749,902` candidates.

Observed RSS increased with the larger indexes and candidate sets. The
threshold-250 country pass reached approximately `4.9 GB` for S2 and `5.8 GB`
for S3 in this process. These values are process RSS observations, not
isolated allocation measurements.

## Representation comparison

`name_clean_unicode` was consistently better than `name_nopunct` at the same
frequency threshold:

- At threshold 100:
  - S2: `30.880%` versus `28.692%`
  - S3: `30.141%` versus `27.881%`
- At threshold 250:
  - S2: `38.983%` versus `37.802%`
  - S3: `38.265%` versus `37.142%`

The compact representation did not compensate for its punctuation removal in
this token-index design.

## Multi-token strategies

Two-token intersection and sorted signatures were highly selective but
recovered very few true pairs because one of the two selected tokens often
changes, disappears, or is represented differently across sources.

At frequency threshold 100:

| Target | Strategy | Pair recall | Candidates | Avg/S1 | P95 | P99 | Max |
|---|---|---:|---:|---:|---:|---:|---:|
| S2 | Two-token intersection, Unicode | 3.957% | 76,187 | 0.173 | 1 | 4 | 63 |
| S2 | Two-token signature, Unicode | 3.596% | 69,203 | 0.157 | 1 | 4 | 56 |
| S3 | Two-token intersection, Unicode | 3.808% | 77,080 | 0.175 | 1 | 5 | 76 |
| S3 | Two-token signature, Unicode | 3.369% | 68,679 | 0.156 | 0 | 4 | 61 |

These strategies should not be used as the primary candidate pass. They may
be useful as an optional precision-oriented pass only if unioned with a
high-recall strategy.

## M3.5 category recovery analysis

The following rates are measured on the 10,000 sampled M3.5 misses per source.
They are actual candidate-set recovery rates for the M4 runs, not the earlier
diagnostic heuristics.

### Country + Unicode rare token, S1→S2

| Category | Freq ≤50 | Freq ≤100 | Freq ≤250 |
|---|---:|---:|---:|
| Abbreviation variation | 22.97% | 32.87% | 41.88% |
| Legal suffix variation | 28.62% | 39.01% | 49.52% |
| Additional/missing tokens | 29.14% | 39.38% | 45.68% |
| Word-order change | 28.99% | 41.30% | 53.33% |
| Typo/spelling variation | 11.05% | 14.73% | 21.53% |
| Weak name/address informative | 9.69% | 14.37% | 19.04% |

### Country + Unicode rare token, S1→S3

| Category | Freq ≤50 | Freq ≤100 | Freq ≤250 |
|---|---:|---:|---:|
| Abbreviation variation | 21.88% | 32.12% | 40.68% |
| Legal suffix variation | 25.18% | 36.73% | 46.19% |
| Additional/missing tokens | 24.75% | 35.06% | 43.03% |
| Word-order change | 27.13% | 36.44% | 48.11% |
| Typo/spelling variation | 11.57% | 16.71% | 21.85% |
| Weak name/address informative | 9.95% | 14.39% | 18.52% |

The token pass improves all four major M3.5 categories, especially at the
larger thresholds, but the recall gain carries a clear candidate and memory
cost.

## Frequency observations

The artifact records the number of distinct tokens at or below every tested
threshold and the ten most frequent tokens for each source and representation.
The threshold sweep demonstrates that a lower cutoff is highly selective but
does not materially improve recall, while threshold 100–250 provides
substantial incremental recall at increasing candidate cost.

No arbitrary candidate cap was applied. Oversized blocks were measured rather
than silently truncated.

## M4 conclusion

Rare-token blocking is the first strategy that materially closes the exact-name
recall gap without approximate retrieval:

- approximately `31%` pair recall at frequency threshold 100;
- approximately `38–39%` pair recall at threshold 250;
- complete entity recovery reaches approximately `36–43%`.

The threshold-250 pass has the strongest measured recall but increases average
candidates to approximately `34` per Source 1 entity and raises memory toward
multi-gigabyte levels. Threshold 100 is a more moderate experimental point.

Multi-token intersection/signature passes are too restrictive as standalone
strategies. Address blocking remains the next unimplemented family and should
be evaluated before selecting the final multi-pass candidate union.
