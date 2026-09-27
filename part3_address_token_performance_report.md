# M5.2.1 — Address-Token Blocking Performance Audit

## Scope

This checkpoint audits and optimizes the existing M5.2 experiment without
changing its address-token strategy, six thresholds, validation split, metrics,
or candidate definitions. M5.3 postal/address-number blocking was not started.

Implementation:
[`src/part3_address_blocking.py`](./src/part3_address_blocking.py)

## Original profiled run

The original M5.2 implementation was run unchanged across both target sources,
all six thresholds, and the same deterministic validation split.

| Measure | Original |
|---|---:|
| Wall-clock time | 2,197.76 s |
| Shell wall-clock time | 2,199.62 s |
| CPU time | 2,064.98 s |
| Peak RSS | 4,207.95 MB |

The wall-clock duration is approximately 36.6 minutes for this environment.

### Original operation counts

| Operation | Count |
|---|---:|
| S2 full scans | 7 |
| S3 full scans | 7 |
| Source 1 full scans | 12 |
| Target index rebuilds | 12 |
| Address-token recomputations | 77,537,913 |
| Source 1 query passes | 12 |
| M4-missed recovery runs | 2 |

### Original phase timings

| Phase | Seconds |
|---|---:|
| Address normalization/tokenization | 115.27 |
| Index construction | 1,425.93 |
| Candidate retrieval/deduplication | 241.23 |

The dominant cause was repeated target-source work: each threshold rebuilt a
country-token index by rescanning and retokenizing the full target source.
Source 1 validation rows were also rescanned for every threshold. M4 missed-pair
analysis was repeated once per source but was not the main cost.

## Optimization

The optimized implementation:

- computes target address tokens and frequencies once per source;
- builds all six threshold views during one additional target scan;
- loads and normalizes validation Source 1 address rows once per source;
- queries each threshold index from the reusable normalized validation rows;
- preserves separate per-threshold candidate sets and metric evaluation;
- retains the existing M4 missed-pair comparison.

No candidate cap, threshold reduction, or strategy change was introduced.

## Optimized profiled run

| Measure | Original | Optimized | Change |
|---|---:|---:|---:|
| Wall-clock time | 2,197.76 s | 442.92 s | 4.96× faster |
| Shell wall-clock time | 2,199.62 s | 445.57 s | 4.94× faster |
| CPU time | 2,064.98 s | 440.03 s | 4.69× lower |
| Peak RSS | 4,207.95 MB | 5,043.76 MB | +835.81 MB |

The optimization substantially reduces runtime but increases peak RSS by
retaining reusable threshold indexes. This memory tradeoff is explicit and
must be considered before final M5 integration.

### Optimized operation counts

| Operation | Count |
|---|---:|
| S2 full scans | 2 |
| S3 full scans | 2 |
| Source 1 full scans | 2 |
| Logical threshold indexes built | 12 |
| Address-token recomputations | 21,523,168 |
| Source 1 query passes | 2 |
| M4-missed recovery runs | 2 |

### Optimized phase timings

| Phase | Seconds |
|---|---:|
| Address normalization/tokenization | 85.72 |
| Index construction | 119.72 |
| Candidate retrieval/deduplication | included in reusable-row query path |

## Output-equivalence validation

The original and optimized JSON results were compared after excluding
profiling/timing/resource metadata. Exact equality was verified for every
semantic metric field for all 12 runs, including:

- pair recall
- complete entity recall
- candidate pairs
- candidate distributions
- zero-candidate counts
- reduction ratios
- M4-missed recovery counts/rates
- missing-address and informative-token counts
- all address block distributions

The optimized artifact is:
[`part3_address_token_optimized_results_v2.json`](./data/processed/part3_address_token_optimized_results_v2.json)

## Decision

The output-equivalent optimization is committed separately. M5.2 is now
materially faster, but peak memory is higher. No final threshold was selected,
and M5.3 has not started.
