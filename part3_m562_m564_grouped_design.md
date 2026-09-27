# M5.6.2–M5.6.4 Grouped Downstream Matching Design

## Status and scope

This document groups the design work for:

- M5.6.2 candidate persistence and reconstruction;
- M5.6.3 pairwise feature, label, and evaluation contracts;
- M5.6.4 downstream matcher benchmark design.

This is a design-only checkpoint. No candidate identities were generated or
reconstructed, no matcher was implemented, and no benchmark was run.

The design does not select a final blocking architecture. It uses only the
locked M5.4/M5.5 evidence and the approved M5.6.1 contract.

## Evidence boundaries

### Measured

- Cumulative identity-union experiments measured thresholds 5, 25, and 250.
- Thresholds 10, 50, and 100 were not cumulatively evaluated.
- M4, M4 ∪ M5.2, and M5.3.3 cumulative stages have measured aggregate
  metrics for S2 and S3.
- M5.3.4 added zero candidate identities, pairs, and complete entities at
  measured thresholds 5, 25, and 250.
- Committed result artifacts do not contain complete reusable per-S1
  candidate identities.
- Blocking peak RSS was approximately 7.23 GB for M5.4, 7.62 GB for
  threshold 5, and 8.44 GB for threshold 25.

### Derived

- Candidate growth, marginal candidate cost, pair recall, complete entity
  recall, and zero-candidate counts from committed identity-union metrics.

### Modeled

- M5.5.2 scoring-time and memory scenarios are estimates, not matcher
  measurements.

### Hypothesis

- A matcher benchmark using persisted candidate identities will reveal quality
  and resource behavior not inferable from blocking recall.

### Open questions

- Acceptable downstream candidate volume and matcher resource budget.
- Matcher formulation and abstention policy.
- Whether threshold-sensitive M5.3.3 additions justify their measured cost.
- Whether M5.3.4 implementation overhead warrants additional investigation.

## 1. Candidate persistence and reconstruction design

### 1.1 Required benchmark stages

The first benchmark will use only these candidate stages:

1. M4 only;
2. M4 ∪ M5.2;
3. M4 ∪ M5.2 ∪ M5.3.3 at threshold 5;
4. M4 ∪ M5.2 ∪ M5.3.3 at threshold 25;
5. M4 ∪ M5.2 ∪ M5.3.3 at threshold 250.

S2 and S3 are persisted and evaluated separately for every stage.

M5.3.4-inclusive stages are not required for the first persistence milestone.
They may be added only if the existing validated logic can produce them
without material additional resource cost and after review. No threshold
10/50/100 stage is in scope.

### 1.2 Reconstruction authority

Because the committed artifacts contain metrics but not candidate rows, a
later approved persistence/reconstruction checkpoint must reconstruct the
candidate identities from the locked blocking implementations.

Reconstruction must use:

- the locked validation split: 20%, seed 42, Source-1 entity split;
- the exact source and target inputs used by the committed experiments;
- the approved M4, M5.2, M5.3.3, and union semantics;
- the exact threshold for each stage;
- empty-signal exclusion;
- multiple-value union semantics;
- country-aware behavior;
- no candidate cap;
- no Cartesian product;
- no ground-truth filtering during candidate creation.

The reconstruction checkpoint must compare its aggregate output with the
corresponding committed artifact before any matcher input is accepted.

### 1.3 Logical storage schema

The persisted dataset consists of three logical components.

#### Candidate rows

One row represents one unique candidate identity:

```text
target_source: "S2" | "S3"
s1_id: canonical Source-1 identifier
target_id: canonical target identifier
stage_id: stable stage name
threshold: integer
blocking_families: canonical sorted list
signal_availability: canonical availability flags
candidate_order: deterministic integer
```

The identity key is:

```text
(target_source, s1_id, target_id)
```

`stage_id` and `threshold` are dataset metadata and must also be checked
against the manifest.

#### Source-1 manifest

Every validation S1 entity receives one manifest row:

```text
target_source
s1_id
candidate_count
has_candidates
zero_candidate_reason
coverage_status
```

`coverage_status` is evaluation-only metadata and is not supplied as a model
feature unless explicitly defined later without label leakage.

#### Dataset manifest

The dataset manifest records:

- schema version;
- stage and threshold;
- target source;
- split fraction, seed, and split identifier;
- input file checksums;
- semantics/version identifiers;
- candidate-row count;
- unique candidate-key count;
- S1 count;
- zero-candidate count;
- duplicate count;
- partition list;
- content checksums;
- Python and dependency versions;
- creation and validation metadata;
- peak RSS, wall time, CPU time, and disk observations.

### 1.4 Physical storage requirements

The implementation may select a columnar or line-oriented format later, but
the format must support:

- streamed or chunked writes;
- bounded-memory reads;
- partitioning by target source and S1 ranges;
- grouped retrieval by S1;
- exact row-count validation;
- deterministic iteration;
- checksum generation;
- preservation of S1 entities with zero rows;
- independent S2/S3 replay.

Candidate data must not be held as a duplicated full in-memory map when a
streaming representation is sufficient.

### 1.5 Identity and replay validation

For each stage and target, persistence validation must prove:

1. every candidate key is unique;
2. persisted row count equals the reconstructed row count;
3. unique-key count equals row count;
4. per-S1 candidate counts match the reconstruction stream;
5. all validation S1 entities appear in the S1 manifest;
6. zero-candidate S1 identities are preserved;
7. S2 and S3 are not mixed;
8. no candidate cap was applied;
9. no Cartesian product was introduced;
10. no ground-truth filter was applied;
11. serialization/deserialization preserves exact candidate sets;
12. content checksums are stable on replay.

Any mismatch stops the checkpoint. The affected stage must not be sent to a
matcher.

## 2. Pairwise feature contract

### 2.1 Feature groups

The first matcher design will expose raw pairwise features in explicit,
typed groups. The exact model may select a subset only after feature
validation.

#### Identity and text features

- normalized name exact agreement;
- normalized name token overlap;
- normalized name character similarity;
- name length difference;
- name missingness flags.

#### Address features

- normalized address exact agreement;
- address token overlap;
- address token containment in each direction;
- address-number agreement;
- address-number availability flags;
- address missingness flags.

#### Postal and country features

- normalized postal exact agreement;
- postal availability flags;
- country exact agreement;
- country missingness flags.

#### Optional contact features

If fields exist and are approved for the target source:

- normalized phone agreement/similarity;
- normalized email agreement;
- contact-field availability and missingness.

No feature may be assumed available until its source coverage is measured.

#### Candidate provenance features

Candidate provenance may include label-independent indicators:

- whether M4 generated the candidate;
- whether M5.2 generated the candidate;
- whether M5.3.3 generated the candidate;
- number of blocking families that produced the candidate;
- signal availability at blocking time.

Provenance must never include ground-truth match status or a value derived
from evaluation labels.

### 2.2 Feature typing and missingness

Every feature must declare:

- type;
- units or range;
- missing-value representation;
- normalization procedure;
- whether it is fitted on training data;
- whether it is available at competition-test inference time.

Missingness must not be silently converted into equality. Empty strings,
invalid normalized values, and unavailable fields receive explicit flags and
non-match-safe values.

### 2.3 Fit boundaries

Any learned vocabulary, frequency statistic, scaler, imputer, calibration,
embedding, or model parameter is fit on training data only.

Validation data is used for evaluation and approved model selection.
Competition test data is inference-only.

Deterministic normalization rules that do not learn from data may be shared
across splits, but their version must be recorded.

## 3. Label and evaluation contract

### 3.1 Pair labels

For evaluation and training only, a candidate pair receives a positive label
when its `(S1, target)` identity is present in the approved ground-truth
mapping for the same target source and split.

Candidate construction must complete before ground-truth lookup.

Labels must be generated separately for S2 and S3. No label is created for a
candidate from a different target source.

### 3.2 Entity-level labels

Evaluation must report both pair-level and S1-level outcomes:

- pair precision, recall, and F-score;
- top-1 and top-k target accuracy;
- complete entity recall;
- unmatched or abstention rate;
- candidate-to-match conversion;
- zero-candidate rate;
- incomplete entity coverage.

If an S1 has multiple true targets, the evaluation contract must specify
whether all true targets are accepted, whether ranking is measured, and how
top-k results are scored.

If an S1 has no true target, false positive and abstention behavior must be
reported explicitly.

### 3.3 Zero-candidate and incomplete entities

Zero-candidate entities remain in all denominators.

The benchmark must distinguish:

- no candidates because required signals were unavailable;
- no candidates because no index key matched;
- candidates present but no true pair recovered;
- candidates present with incomplete entity coverage;
- candidates present with complete entity coverage.

The initial benchmark must not invent a fallback candidate set. Any fallback
or abstention policy is a separate model behavior that must be measured.

## 4. Matcher formulation

### 4.1 Initial formulation

The first empirical benchmark will use a pairwise binary classifier with
per-S1 candidate ranking:

1. compute features independently for each persisted candidate pair;
2. score each pair with a train-only fitted binary model;
3. rank candidates within each S1 by score;
4. apply an explicitly configured acceptance threshold or abstention rule;
5. report top-1, top-k, pair-level, and entity-level metrics.

This formulation is chosen as a benchmark interface, not as a final model
decision. It provides a direct way to measure candidate conversion and
resource use before considering more complex ranking or entity-level models.

### 4.2 Baselines

The benchmark design should include simple deterministic baselines where
feasible:

- exact normalized-name agreement;
- exact agreement on a high-confidence available signal combination;
- fixed-score or rule-based abstention baseline.

Baselines are comparison instruments only. They do not define the final
architecture.

### 4.3 Training protocol

Training must:

- use only training labels;
- avoid duplicate pair leakage across train and validation;
- preserve S2/S3 separation;
- record the model, feature, and normalization versions;
- use deterministic seeds;
- preserve candidate-stage provenance;
- avoid fitting on competition-test rows.

The split strategy for model training must be defined before execution and
must not change the locked blocking validation split without review.

## 5. Benchmark stages and comparisons

The initial benchmark compares the following persisted stages independently:

| Stage | Threshold | Target sources |
|---|---:|---|
| M4 | 250 semantics | S2, S3 |
| M4 ∪ M5.2 | 250 baseline | S2, S3 |
| M4 ∪ M5.2 ∪ M5.3.3 | 5 | S2, S3 |
| M4 ∪ M5.2 ∪ M5.3.3 | 25 | S2, S3 |
| M4 ∪ M5.2 ∪ M5.3.3 | 250 | S2, S3 |

No threshold 10, 50, or 100 benchmark stage is planned.

M5.3.4-inclusive stages are deferred unless persistence is already available
or the approved reconstruction implementation can produce them within the
same resource envelope without duplicating candidate maps.

## 6. Benchmark measurements

### Quality

- pair precision, recall, and F-score;
- complete entity recall;
- top-1 and top-k entity accuracy;
- unmatched and abstention rates;
- candidate-to-match conversion;
- error categories by candidate count, missingness, and blocking provenance.

### Runtime and resources

- feature computation wall time and CPU time;
- model scoring wall time and CPU time;
- end-to-end matcher wall time;
- peak matcher RSS;
- disk used by persisted candidates and intermediate features;
- serialization/deserialization time;
- candidate throughput;
- batch-size sensitivity;
- per-S1 latency distribution where measurable.

Blocking RSS must remain a separate field from matcher RSS.

### Required bounded microbenchmark before full benchmark

Before full matcher execution, M5.6.6 must run a deterministic bounded
microbenchmark from persisted identities. Its sample must include:

- low candidate-count S1 entities;
- P95/P99 and maximum candidate-count S1 entities;
- missing signal cases;
- multiple-candidate cases;
- complete and incomplete entities;
- zero-candidate entities in the control accounting, even though they have no
  pair rows.

The sample selection algorithm, seed, stage, target source, and checksums must
be recorded.

## 7. Resource limits and stopping rules

### Known measured references

- M5.4 blocking peak RSS: approximately 7.23 GB;
- threshold-5 blocking peak RSS: approximately 7.62 GB;
- threshold-25 blocking peak RSS: approximately 8.44 GB.

These are observations, not matcher limits.

### Required execution controls

Before persistence or benchmarking is authorized, define:

- maximum RSS for the active process;
- maximum temporary disk usage;
- maximum wall time and CPU time;
- partition/chunk size;
- maximum concurrent target sources;
- abort behavior and cleanup policy.

Processing must use Python 3.11, one target source at a time, streamed or
chunked operations, and continuous resource telemetry.

Stop immediately on:

- unexpected RSS growth;
- disk pressure;
- candidate-count mismatch;
- duplicate identities;
- split or target-source contamination;
- semantics mismatch;
- evidence of ground-truth filtering;
- serialization/replay inequality.

## 8. Leakage controls

The following controls are mandatory:

1. Candidate construction occurs without ground-truth labels.
2. Ground truth is read only after candidate construction for labels and
   evaluation.
3. Feature fitting uses training data only.
4. Validation labels do not affect normalization, candidate construction,
   feature fitting, or unapproved model selection.
5. Competition-test data is inference-only.
6. Candidate provenance is label-independent.
7. Duplicate candidates do not multiply labels or metrics.
8. S2 and S3 data, labels, and metrics remain isolated.
9. Split membership and input checksums are carried in manifests.
10. No manually curated match exceptions are introduced.

## 9. Expected outputs

The grouped design expects the later milestones to produce:

- candidate persistence/reconstruction implementation;
- per-stage, per-target candidate identity artifacts;
- S1 manifests preserving zero-candidate entities;
- replay-validation and checksum manifests;
- pairwise feature specification and implementation;
- label/evaluation specification;
- deterministic matcher benchmark configuration;
- bounded microbenchmark artifact;
- full matcher benchmark artifact;
- resource telemetry;
- leakage audit;
- final M5.6.7 evidence handoff.

None of those execution artifacts is created by this design checkpoint.

## 10. Dependencies and review gates

The following dependency order is mandatory:

1. Review and approve this grouped design.
2. Implement candidate persistence/reconstruction and validate identities.
3. Stop for review before matcher feature work is benchmarked.
4. Run the bounded microbenchmark.
5. Stop for review.
6. Run the full matcher benchmark using persisted identities only.
7. Stop for review before any architecture decision.

The next implementation milestone must be candidate persistence/reconstruction
and identity validation. It may regenerate identities only under explicit
approval and must not alter locked prior artifacts.

## 11. Proposed commit boundaries

This grouped design is one meaningful commit:

`docs: design M5.6 persistence and matcher benchmark`

Later grouped execution milestones should commit:

- candidate persistence/replay validation;
- microbenchmark evidence;
- full matcher benchmark evidence;
- final M5.6.7 handoff.

No candidate generation, matcher implementation, or benchmark is authorized
by this document.
