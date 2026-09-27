# M5.6.1 Downstream Candidate Contract

## Scope and status

This is the M5.6.1 contract-design checkpoint. It defines the downstream
blocking-to-matching interface, schema, provenance, zero-candidate handling,
S2/S3 separation, deterministic ordering, and replay requirements.

No candidate sets were generated, no candidate identities were reconstructed,
no matcher was built, and no benchmark was run. M4/M5.2/M5.3/M5.4/M5.5
implementations and artifacts remain unchanged.

The contract does not select a final blocking architecture.

## Candidate identity availability audit

### Audit question

Do the committed M5.4 and M5.5 cumulative result artifacts contain complete,
reusable per-S1 candidate identities that can be passed directly to a
downstream matcher?

The audit distinguishes identity evidence used during an experiment from
identity data persisted in the committed artifact. Aggregate candidate counts,
recall, marginal arithmetic, and statements that identity unions were used do
not by themselves establish replayability.

### Audited committed artifacts

| Artifact | Stages represented | Persisted per-S1 candidate identities? | Persisted flat `(s1_id, target_id)` rows? | Replay status |
|---|---|---|---|---|
| `part3_m54_m4_m52_union_results.json` | M4, M5.2, M4 ∪ M5.2; threshold 250 | No | No | Not directly replayable |
| `part3_m54_m4_m52_m533_union_results.json` | M4, M5.2, M5.3.3, cumulative union; threshold 250 | No | No | Not directly replayable |
| `part3_m54_m4_m52_m533_m534_union_results.json` | M4, M5.2, M5.3.3, M5.3.4, full union; threshold 250 | No | No | Not directly replayable |
| `part3_m553_threshold5_results.json` | cumulative threshold 5 result; M4/M5.2 baseline reused | No | No | Not directly replayable |
| `part3_m553_threshold25_results.json` | cumulative threshold 25 result; M4/M5.2 baseline reused | No | No | Not directly replayable |
| M5.5.1 normalized artifact | normalized threshold-250 metrics and provenance | No | No | Metrics only |
| M5.5.2 cost model artifact | measured candidate-count inputs and modeled scenarios | No | No | Metrics/model only |
| M5.5.4 comparison artifact | copied/derived architecture evidence | No | No | Comparison only |

The audited JSON result files contain top-level metadata such as checkpoint,
configuration, threshold, validation metadata, source strategy summaries,
candidate-pair totals, distributions, marginal counts, resource observations,
and semantic checks. They do not contain a complete candidate map keyed by
S1, a flat candidate-pair table, or a serialized identity manifest.

### Audit conclusion

The committed artifacts contain **aggregate and derived identity evidence but
not complete reusable candidate identities**.

Therefore:

1. The existing results are sufficient for the committed blocking trade-off
   analysis.
2. They are not sufficient to replay candidate pairs into a downstream
   matcher.
3. A **candidate-persistence/reconstruction checkpoint is required** before
   the M5.6.4 matcher benchmark.
4. “No candidate regeneration” applies only after reusable candidate identity
   artifacts have been established and validated.
5. Candidate reconstruction, if later approved, must use the locked
   semantics and exact validation split; it must not silently change a
   threshold, source separation, cap, or blocking rule.

The audit applies to every candidate stage considered for M5.6.4, not only
M5.3.4:

- M4 only;
- M4 ∪ M5.2;
- M4 ∪ M5.2 ∪ M5.3.3 at thresholds 5, 25, and 250;
- M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 at thresholds 5, 25, and 250.

None currently has a committed replayable per-S1 identity artifact.

## Evidence classification

### Measured

- Candidate identity unions were computed during the M5.4 and M5.5
  experiments.
- Aggregate candidate-pair totals and per-S1 distribution metrics were
  persisted.
- Cumulative thresholds 5, 25, and 250 were measured.
- Thresholds 10, 50, and 100 were not cumulatively evaluated.
- S2 and S3 were processed as separate target sources.
- Ground truth was not used to construct candidate indexes or candidates.

### Derived

- Marginal candidate counts.
- Candidate growth.
- Candidate cost.
- Recall and complete-entity metrics.
- Zero-candidate counts.

These values do not substitute for candidate identity rows.

### Modeled

M5.5.2 scoring-time and memory scenarios are not matcher measurements and
must not be treated as interface or resource guarantees.

### Hypothesis

A downstream matcher can be benchmarked reproducibly only after candidate
identity persistence, schema validation, and replay checks succeed.

### Open question

Whether candidate reconstruction is feasible within the locked semantics and
resource envelope remains unresolved.

## Downstream candidate contract

The blocking layer must expose a versioned candidate dataset with one logical
record per unique candidate pair:

```text
CandidatePair {
    schema_version: string
    split_id: string
    target_source: enum["S2", "S3"]
    s1_id: stable_source1_identifier
    target_id: stable_target_identifier
    blocking_stage: string
    threshold: integer
    blocking_families: set[string]
    signal_availability: object
    candidate_order: integer
}
```

The physical serialization format is not selected by this checkpoint. Any
format must preserve the logical fields and validation rules below.

### Required identity rules

- `(target_source, s1_id, target_id)` is the candidate identity key.
- Duplicate keys are invalid in a serialized stage.
- S2 and S3 candidate identities must never share a candidate namespace
  without an explicit `target_source` field.
- Candidate rows must refer to the declared validation or inference split.
- Identifiers must be preserved exactly; display formatting must not alter
  identity.
- Candidate generation must not use ground-truth labels.
- No arbitrary candidate cap is permitted.
- No Cartesian product may be introduced during persistence or replay.

### Required stage metadata

Each candidate dataset must include a manifest containing:

- checkpoint and artifact identifier;
- blocking stage name;
- target source;
- threshold;
- validation split identifier;
- split fraction and seed where applicable;
- Source-1 entity count;
- input file identifiers or checksums;
- blocking semantics version;
- extraction and empty-signal rules;
- candidate row count;
- unique S1 count;
- zero-candidate S1 count;
- duplicate count;
- ordering specification;
- creation environment;
- creation timestamp;
- content checksum.

## Schema and storage requirements

### Logical tables

The minimum logical representation consists of:

1. **Candidate rows**
   - `target_source`
   - `s1_id`
   - `target_id`
   - `blocking_stage`
   - `threshold`
   - `blocking_families`
   - `signal_availability`
   - `candidate_order`

2. **S1 manifest**
   - `target_source`
   - `s1_id`
   - `candidate_count`
   - `has_candidates`
   - `zero_candidate_reason`
   - `entity_coverage_status`

3. **Dataset manifest**
   - schema and semantics version;
   - split and source metadata;
   - row and identity counts;
   - checksums;
   - resource metadata;
   - provenance.

The S1 manifest is required even when the candidate rows are empty for an
S1, so zero-candidate entities are not silently dropped.

### Storage properties

The eventual physical format must support:

- streaming writes;
- partitioning by target source and, if needed, S1 ranges;
- bounded-memory reads;
- deterministic iteration;
- exact row-count and checksum validation;
- random or grouped access by S1 for matching;
- independent S2 and S3 replay;
- preservation of empty candidate groups.

The storage format and partition size require a later design decision after
candidate persistence/reconstruction feasibility is assessed.

## Provenance requirements

Every candidate stage considered by M5.6.4 must carry provenance identifying:

- M4, M5.2, M5.3.3, and M5.3.4 membership;
- threshold used by each threshold-sensitive family;
- country-aware and signal-family semantics;
- empty-key exclusion behavior;
- multiple-value union behavior;
- cross-family intersection behavior where applicable;
- source target (`S2` or `S3`);
- validation split and seed;
- implementation and schema version;
- whether identities were persisted directly or reconstructed.

Provenance must describe candidate construction, not encode ground-truth
match status.

## S2/S3 separation

S2 and S3 are separate candidate populations and separate downstream
evaluation targets.

Required controls:

- separate manifests;
- separate candidate namespaces or mandatory `target_source`;
- separate counts and checksums;
- separate replay;
- separate feature distributions where relevant;
- separate labels and evaluation metrics;
- no cross-target joins;
- no pooling of S2 and S3 metrics into a single recall or resource result.

## Zero-candidate and incomplete-entity representation

An S1 entity must remain represented in the S1 manifest even when it has no
candidate rows.

Required states:

- `zero_candidates_missing_signals`;
- `zero_candidates_no_matching_index_keys`;
- `zero_candidates_filtered_or_invalid_keys`;
- `has_candidates_incomplete_entity_coverage`;
- `has_candidates_complete_entity_coverage`;
- `coverage_unknown` only when the evaluation source does not provide labels.

Ground-truth-derived coverage fields may be populated only in evaluation
artifacts after candidate construction. They must not be written into the
candidate input consumed by a production matcher.

The matcher contract must preserve:

- zero-candidate count;
- candidate count distribution;
- candidate-present but no-true-match cases;
- incomplete entity cases;
- abstention or unmatched output, if the matcher supports it.

No zero-candidate S1 may be silently discarded from evaluation denominators.

## Deterministic ordering

The candidate dataset must define a stable order:

1. `target_source`;
2. `s1_id` using the canonical identifier sort;
3. `candidate_order`, assigned from a deterministic sort of `target_id`;
4. tie-breakers, if target IDs are not totally orderable.

Blocking-family provenance is a set and must be serialized canonically, such
as sorted family names. Serialization must not depend on hash iteration order.

If a downstream model requires ranking input order, the ranking order must be
declared separately from identity order. Candidate order must not imply match
probability.

## Replay requirements

Replay is not authorized yet because the audited committed artifacts do not
contain candidate identities.

Before any matcher benchmark, a later candidate-persistence/reconstruction
checkpoint must establish, for every M5.6.4 stage:

1. complete per-S1 candidate identities;
2. exact total candidate-row count;
3. exact unique-key count;
4. exact per-S1 candidate counts;
5. exact zero-candidate S1 set;
6. S2/S3 separation;
7. stage and threshold metadata;
8. deterministic ordering;
9. duplicate absence;
10. no candidate cap or Cartesian expansion;
11. content checksum;
12. replay equality after serialization and deserialization.

For reconstructed identities, the checkpoint must additionally prove:

- the locked validation split is unchanged;
- the approved blocking semantics are unchanged;
- the reconstruction code version is recorded;
- aggregate metrics match the committed artifact within a declared exact
  tolerance;
- any mismatch stops the checkpoint and prevents matcher benchmarking.

The reconstruction checkpoint may regenerate candidate identities only after
explicit approval. It must not modify the committed M4/M5.2/M5.3/M5.4/M5.5
artifacts.

## Candidate stages requiring identity availability before M5.6.4

| M5.6.4 stage | Required identity artifact before benchmark | Current status |
|---|---|---|
| M4 only, S2 | per-S1 M4 candidate identities | unavailable |
| M4 only, S3 | per-S1 M4 candidate identities | unavailable |
| M4 ∪ M5.2, S2 | per-S1 cumulative union identities | unavailable |
| M4 ∪ M5.2, S3 | per-S1 cumulative union identities | unavailable |
| M4 ∪ M5.2 ∪ M5.3.3(5), S2/S3 | per-S1 threshold-5 identities | unavailable |
| M4 ∪ M5.2 ∪ M5.3.3(25), S2/S3 | per-S1 threshold-25 identities | unavailable |
| M4 ∪ M5.2 ∪ M5.3.3(250), S2/S3 | per-S1 threshold-250 identities | unavailable |
| Full union with M5.3.4 at 5/25/250, S2/S3 | per-S1 full-union identities | unavailable |

This table prevents treating M5.3.4 as the only unavailable stage.

## Required next checkpoint

The next required checkpoint is **candidate persistence/reconstruction and
identity validation**, before M5.6.4 matcher benchmarking.

It must define and obtain approval for:

- whether reconstruction is allowed;
- exact stage scope;
- exact source and split scope;
- resource ceilings;
- output storage location and format;
- identity and checksum validation;
- stopping behavior;
- artifact commit boundaries.

No matcher, pairwise feature pipeline, model training, or benchmark may begin
until that checkpoint establishes reusable candidate identities.

## Validation and stop gate for M5.6.1

This document should be reviewed for:

- contract completeness;
- identity-key correctness;
- zero-candidate preservation;
- S2/S3 isolation;
- deterministic ordering;
- provenance sufficiency;
- replay validation requirements;
- explicit candidate-availability limitations.

M5.6.1 ends here. No candidate generation, reconstruction, matcher
implementation, or benchmark is authorized by this checkpoint.

