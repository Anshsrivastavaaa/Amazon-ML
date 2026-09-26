# Part 3 — M3 Exact-Name Blocking Baseline

## Scope

This is the first blocking evaluation cycle. It intentionally contains only:

- Safe Unicode exact-name blocking.
- Compact/no-punctuation exact-name blocking.
- Country + Safe Unicode exact-name blocking.
- The union of Safe Unicode name-only and country + name.

Token, address, postal, character n-gram, and approximate retrieval strategies
were not implemented.

The implementation is in
[`src/part3_blocking.py`](./src/part3_blocking.py). The structured results are
in [`data/processed/part3_baseline_results.json`](./data/processed/part3_baseline_results.json).

## Validation design

- Dataset: training Source 1, Source 2, Source 3, and ground truth.
- Split unit: Source 1 entity.
- Validation fraction: 20%.
- Seed: 42.
- Validation entities: 441,365.
- Validation split was stratified by Source 1 country and ground-truth match
  bucket (`0`, `1`, `2+`).
- Target indexes were built from source records only; ground-truth labels were
  used only after candidate generation for evaluation.
- S2 and S3 were evaluated separately.
- Candidate generation was chunked at 100,000 rows.

The measured full comparison denominators use:

```text
441,365 × 5,034,616  for S1→S2
441,365 × 5,285,603  for S1→S3
```

## Metrics

- Pair recall:
  `recovered true target IDs / all true target IDs`.
- Complete entity recall:
  fraction of validation S1 entities for which all true target IDs were
  recovered.
- Candidate count statistics are per validation S1 entity.
- Reduction ratio:
  `1 - candidate_pairs / validation_S1_entities × target_source_rows`.
- Memory is the observed process RSS at metric collection time, not an isolated
  per-index allocation measurement.

## S1→S2 results

| Strategy | Pair recall | Complete entity recall | Candidates | Avg | Median | P95 | P99 | Max | Zero candidates | Reduction ratio | Runtime (s) | RSS (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Name only | 15.622% | 19.513% | 1,515,876 | 3.435 | 0 | 20 | 70 | 192 | 242,259 | 99.999932% | 44.87 | 3,344 |
| Compact name | 21.409% | 22.341% | 2,064,942 | 4.679 | 1 | 30 | 88 | 224 | 207,325 | 99.999907% | 49.55 | 3,348 |
| Country + name | 15.622% | 19.513% | 1,511,539 | 3.425 | 0 | 20 | 70 | 192 | 242,411 | 99.999932% | 47.56 | 3,335 |
| Name ∪ country + name | 15.622% | 19.513% | 1,515,876 | 3.435 | 0 | 20 | 70 | 192 | 242,259 | 99.999932% | 92.42 | 3,335 |

S1→S2 contained 739,298 true positive target pairs in validation.

## S1→S3 results

| Strategy | Pair recall | Complete entity recall | Candidates | Avg | Median | P95 | P99 | Max | Zero candidates | Reduction ratio | Runtime (s) | RSS (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Name only | 15.874% | 18.426% | 1,656,422 | 3.753 | 0 | 21 | 69 | 200 | 232,230 | 99.999929% | 48.41 | 4,022 |
| Compact name | 22.187% | 21.442% | 2,279,905 | 5.166 | 1 | 31 | 88 | 235 | 195,698 | 99.999902% | 47.34 | 4,035 |
| Country + name | 15.874% | 18.426% | 1,648,535 | 3.735 | 0 | 20 | 69 | 192 | 232,343 | 99.999929% | 50.69 | 4,019 |
| Name ∪ country + name | 15.874% | 18.426% | 1,656,422 | 3.753 | 0 | 21 | 69 | 200 | 232,230 | 99.999929% | 99.10 | 4,019 |

S1→S3 contained 789,453 true positive target pairs in validation.

## Findings

### Country as an experimental signal

Country + name did not improve recall in this evaluation. It removed a small
number of candidates while recovering the same number of true pairs as
name-only:

- S2 pair recall remained 15.622%, but the country-constrained pass recovered
  fewer true pairs than name-only before rounding.
- S3 pair recall remained 15.874%, with the same behavior.
- The union was identical to name-only because country + name is a subset of
  the name-only key for these records.

Country is therefore not an automatic exclusion rule for future blocking. It
should remain an optional feature/pass and must be evaluated as part of later
multi-signal blocks. France was handled generically because no country
enumeration or hard-coded filter was used.

### Compact name

Compact exact-name blocking increased recall:

- S2: 15.622% → 21.409%.
- S3: 15.874% → 22.187%.

It also increased candidates and reduced zero-candidate entities, but the
absolute recall remains low. This establishes that exact-name-only blocking is
not sufficient and motivates the next evidence-driven blocking families.

### Resource behavior

The baseline never constructs a Cartesian product. It builds target-source
inverted indexes and queries them with validation S1 records. Observed process
RSS reached approximately 3.3 GB during S2 evaluation and 4.0 GB during S3
evaluation. This is a key constraint for later index design and any full-test
run.

## Checkpoint decision

M3 is complete. No token, address, postal, character n-gram, or approximate
blocking strategy is included in this checkpoint. Those strategies require
review of these measured baseline results before implementation.
