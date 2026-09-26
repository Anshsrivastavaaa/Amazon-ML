# Part 2 — Normalization Experiments

## Objective

Part 2 establishes text representations for the later blocking and matching
pipeline. The original `business_name` and `business_address` values remain
unchanged. Derived representations are evaluated against real positive
relationships from the training ground truth and against the complete training
corpora.

The experiment is implemented in
[`src/part2_normalization.py`](./src/part2_normalization.py). Its structured
output is
[`data/processed/part2_normalization_results.json`](./data/processed/part2_normalization_results.json).

## Experimental design

- Source: the actual training TSV files and `train_ground_truth.tsv`.
- Legacy mixed positive-pair sample: 50,000 matched Source 1-to-Source 2/3
  relationships, using the first listed match from each sampled Source 1 row.
- Source-separated positive-pair samples: 50,000 S1↔S2 pairs and 50,000
  S1↔S3 pairs, sampled independently with reservoir sampling over all
  ground-truth match IDs.
- Sampling seed: 42.
- Source files were read in 100,000-row chunks.
- Collision statistics were calculated over all rows in each training source.
- Empty strings were excluded from non-empty collision counts but reported
  separately.

The sampled relationship is the first listed match for each sampled Source 1
row. This measures representation agreement on true cross-source pairs; it is
not a model score and does not estimate final F₀.₅.

## Representations

### Raw

The original string, retained for auditability and later feature comparison.

### Safe Unicode

The primary representation:

1. Convert null-like values to an empty string.
2. Apply Unicode NFKC normalization.
3. Apply Unicode case folding.
4. Collapse whitespace and trim.

This preserves Unicode letters and digits, including non-Latin scripts. It does
not transliterate text and does not remove legal suffixes.

### Compact

An auxiliary representation derived from Safe Unicode by replacing punctuation
with spaces and collapsing whitespace. It is useful for punctuation variation,
but must not be used alone when it creates oversized blocks.

### Experimental legal-suffix stripping

An intentionally aggressive diagnostic representation that removes common
tokens such as `private`, `pvt`, `limited`, `ltd`, `corporation`, `corp`, `inc`,
`llc`, and `llp`.

It is not approved as the sole representation for blocking or matching because
it can merge otherwise distinct businesses.

## Source-separated positive-pair results

The source-separated experiment is the primary confirmation for Part 2. It
contains exactly 50,000 joined pairs for each source relationship:

- S1↔S2: 50,000 pairs.
- S1↔S3: 50,000 pairs.

Levenshtein distance is the ordinary character edit distance. The normalized
similarity is the RapidFuzz normalized Levenshtein similarity in `[0, 1]`.
Token Jaccard uses whitespace-separated tokens from the Safe Unicode view.

### S1↔S2: 50,000 pairs

| Field | Raw exact | Safe Unicode exact | Compact exact | Experimental exact | Mean Lev. distance | Mean Lev. similarity | Mean token Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| Business name | 4.756% | 15.552% | 21.342% | 42.882% | 11.3448 | 0.567870 | 0.553973 |
| Business address | 0.000% | 10.696% | 12.554% | 12.556% | 35.4974 | 0.339538 | 0.584877 |

The matched Source 2 address was empty in 2,356 pairs. Source 1 names and
matched names were non-empty in all sampled pairs.

### S1↔S3: 50,000 pairs

| Field | Raw exact | Safe Unicode exact | Compact exact | Experimental exact | Mean Lev. distance | Mean Lev. similarity | Mean token Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| Business name | 4.740% | 15.854% | 22.152% | 41.170% | 8.6820 | 0.675763 | 0.566626 |
| Business address | 4.398% | 4.406% | 4.408% | 4.408% | 23.3950 | 0.579500 | 0.464156 |

The matched Source 3 address was empty in 2,158 pairs. Source 1 names and
matched names were non-empty in all sampled pairs.

Safe Unicode and Compact improve exact agreement over raw values for both
source pairs. Source 3 has higher mean name similarity and lower mean name
edit distance than Source 2 in this sample. The address behavior differs by
source, reinforcing that address signals should be combined with names and
other derived components rather than treated as a universal exact key.

The full artifact also retains the original mixed sample for continuity:
50,000 rows with 46,042 S1↔S2 and 3,958 S1↔S3 first-match pairs.

| Field | Raw exact | Safe Unicode exact | Compact exact | Experimental exact |
|---|---:|---:|---:|---:|
| Business name | 4.704% | 15.814% | 21.442% | 41.298% |
| Business address | 0.076% | 10.016% | 11.634% | 11.648% |

The conservative Safe Unicode view materially improves exact agreement over
raw text. Compact punctuation handling provides a further improvement. Legal
suffix stripping increases exact name agreement substantially, but the
collision analysis below shows why that transformation must remain auxiliary.

In the legacy mixed sample of 50,000 positive pairs:

- No Source 1 names were empty.
- No matched names were empty.
- 2,206 matched addresses were empty on the Source 2/3 side.

Therefore, empty addresses must never be used as an exact blocking key.

## Collision behavior

Collision statistics are computed over every row in each full training source,
not only the sampled pairs. The artifact stores separate results for
`train_source1`, `train_source2`, and `train_source3`, allowing the S1↔S2 and
S1↔S3 experiments to be interpreted against their actual candidate pools.

The table reports rows belonging to duplicated non-empty values. Larger values
mean more records share a representation and therefore a greater risk of
oversized or ambiguous blocking buckets.

### Business names

| Source | Raw | Safe Unicode | Compact | Experimental |
|---|---:|---:|---:|---:|
| Train Source 1 | 845,385 | 846,097 | 866,894 | 1,047,347 |
| Train Source 2 | 872,386 | 1,169,380 | 1,403,712 | 2,161,948 |
| Train Source 3 | 892,270 | 1,138,818 | 1,405,225 | 2,169,694 |

Maximum non-empty name bucket sizes were:

- Source 1: 253 raw, 253 Safe Unicode, 526 experimental.
- Source 2: 320 raw, 464 Safe Unicode, 708 experimental.
- Source 3: 421 raw, 462 Safe Unicode, 648 experimental.

### Business addresses

| Source | Raw | Safe Unicode | Compact |
|---|---:|---:|---:|
| Train Source 1 | 116,304 | 116,304 | 117,160 |
| Train Source 2 | 949,860 | 1,013,344 | 1,036,864 |
| Train Source 3 | 859,813 | 862,505 | 886,345 |

Maximum non-empty address bucket sizes were 14 for Source 1, 19 for Source 2,
and 29 for Source 3 under Safe Unicode. Address normalization is useful, but
address-only blocks still require country or additional components where
available.

## Decisions for Part 3

1. Keep raw values.
2. Use Safe Unicode as the primary representation for names and addresses.
3. Use Compact as an auxiliary key for punctuation-insensitive blocking.
4. Never use empty normalized values as keys.
5. Keep legal-suffix stripping as an experimental auxiliary view only.
6. Do not hard-code country values; the representation is country-agnostic so
   unseen test countries such as France remain supported.
7. Add collision-aware block-size limits and measure any candidates removed by
   those limits.
8. Combine name and address-derived keys rather than relying on legal-suffix
   stripping or address-only blocking.

## Reproduction

From the repository root, using an environment with the pinned data-analysis
dependencies:

```powershell
python src/part2_normalization.py --sample-size 50000 --chunk-size 100000
```

The command writes the JSON artifact under `data/processed/`. The large raw
datasets are intentionally not committed.
