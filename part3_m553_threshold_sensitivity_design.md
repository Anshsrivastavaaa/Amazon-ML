# M5.5.3 Threshold-Sensitivity Experiment Design

## Status and scope

This is a design-only checkpoint. No candidate sets were generated, no
threshold experiment was executed, and no locked M4, M5.2, M5.3.3, M5.3.4,
or M5.4 artifact was modified.

The design uses the fixed approved protocol:

- validation fraction: 20%;
- seed: 42;
- split unit: Source-1 entity;
- validation universe: 441,365 Source-1 entities;
- targets evaluated separately: S2 and S3;
- Python 3.11;
- target indexes built without ground-truth labels;
- no Cartesian product, candidate cap, or ground-truth-derived index.

The measured M5.4 cumulative baseline is threshold 250 only. This design
does not extrapolate that baseline to lower thresholds.

## Exact questions

1. Does a lower number-frequency threshold provide materially better
   incremental recovery per added candidate than threshold 250?
2. Does M5.3.3 provide additional marginal recovery at lower thresholds when
   added to the actual M4 ∪ M5.2 candidate identities?
3. Does M5.3.4 provide any incremental recovery at lower thresholds when
   added to the actual M4 ∪ M5.2 ∪ M5.3.3 candidate identities?

Standalone recall cannot answer these questions because it does not identify
overlap with M4 or M5.2. Every proposed cumulative run must retain actual
per-S1 candidate identities and compute set differences.

## What is already measured

The committed standalone artifacts already contain threshold rows for 5, 10,
25, 50, 100, and 250:

- M5.3.3 number-only and country+number for S2 and S3;
- M5.3.4 postal+number and country+postal+number for S2 and S3.

Those rows provide standalone pair recall, complete-entity recall, candidate
counts, distribution tails, and zero-candidate counts. They do **not** provide
cumulative M4/M5.2 overlap or cumulative marginal recovery.

The committed M5.4 artifacts provide actual candidate identities only for the
threshold-250 cumulative stages:

- M4;
- M4 ∪ M5.2;
- M4 ∪ M5.2 ∪ M5.3.3;
- M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4.

The lower-threshold cumulative results are therefore not measured.

## Minimum primary experiment

The primary sweep uses four thresholds: **5, 25, 100, and 250**.

This set preserves:

- the lowest available threshold, where candidate cost is smallest;
- a low/intermediate point;
- a high/intermediate point;
- the already measured cumulative endpoint at 250.

Thresholds 10 and 50 are not silently assumed equivalent to neighboring
points. They are reserved for a conditional refinement if the four-point
curve has a material transition between 5→25 or 25→100, or if the decision
criteria cannot distinguish the lower-threshold behavior. This avoids
duplicating six complete cumulative sweeps before knowing whether the
intermediate resolution is needed.

### Experiment T-N — cumulative M5.3.3 number contribution

For each threshold in `{5, 25, 100, 250}`, and for each target S2 and S3
separately:

1. Reuse the fixed M4 and M5.2 semantics and construct their actual
   per-S1 candidate identities for the fixed validation universe.
2. Generate the approved M5.3.3 country+number candidate identities at the
   selected threshold.
3. Form the actual union:
   `M4 ∪ M5.2 ∪ M5.3.3(threshold)`.
4. Evaluate the union against ground truth only after candidate construction.
5. Compute the M5.3.3 marginal difference against the actual
   `M4 ∪ M5.2` identities.

The threshold-250 row must be checked against the committed M5.4.3 artifact
rather than treated as a new independent result.

### Experiment T-C — cumulative M5.3.4 combination contribution

For each threshold in `{5, 25, 100, 250}`, and for each target S2 and S3
separately:

1. Reuse the same fixed M4 and M5.2 candidate identities and the corresponding
   T-N cumulative identities where safe.
2. Generate the exact approved M5.3.4 country+postal+number identities:
   - union values within the postal family;
   - union values within the number family;
   - intersection across postal and number families;
   - country-aware lookup;
   - empty country, postal, and number values excluded;
   - no Cartesian product and no arbitrary cap.
3. Form the actual union:
   `M4 ∪ M5.2 ∪ M5.3.3(threshold) ∪ M5.3.4(threshold)`.
4. Evaluate only after candidate construction.
5. Compute the M5.3.4 marginal difference against the actual preceding
   cumulative identities.

The threshold-250 row must be checked against the committed M5.4.4 artifact.

## Conditional refinement

If the four-point primary sweep leaves a decision boundary unresolved,
execute the same T-N and T-C protocol at thresholds 10 and 50. The refinement
requires explicit approval after review of the primary results; it is not
part of this design checkpoint and must not run automatically.

Examples of unresolved boundaries include a large change in marginal
candidate cost or recovered-pair rate between adjacent primary thresholds,
or a M5.3.4 contribution that changes sign/scale across the primary points.

## Required metrics for every cumulative row

Report S2 and S3 separately, for every threshold and cumulative stage:

- pair recall;
- complete entity recall;
- total candidate pairs;
- average candidates/S1;
- median candidates/S1;
- P95 candidates/S1;
- P99 candidates/S1;
- maximum candidates/S1;
- zero-candidate S1 entities;
- candidate-generation wall runtime;
- candidate-generation CPU time where available;
- peak RSS;
- candidate growth relative to the immediately preceding cumulative stage.

For each addition, report from actual candidate identities:

- newly recovered true pairs;
- newly recovered complete entities;
- marginal candidate pairs;
- marginal candidate cost;
- percentage of previously missed true pairs recovered.

Required formulas:

- candidate growth =
  `(later candidate pairs - earlier candidate pairs) / earlier candidate pairs`;
- marginal candidate cost =
  `marginal candidate pairs / newly recovered true pairs`, or `None` for
  zero newly recovered pairs;
- previously missed pairs recovered =
  `newly recovered true pairs / previously missed true pairs`.

Each artifact field must identify whether it is measured or derived.

## Exact cumulative comparisons

The primary comparison stages are:

| Stage | Candidate identities |
|---|---|
| A | M4 |
| B | M4 ∪ M5.2 |
| C | M4 ∪ M5.2 ∪ M5.3.3(threshold) |
| D | M4 ∪ M5.2 ∪ M5.3.3(threshold) ∪ M5.3.4(threshold) |

The experiment should not spend separate runs reproducing M4-only metrics
when an identity-equivalent result can be reused safely. Stage A/B inputs
must nevertheless be present for every target and threshold comparison, and
their provenance must point to the committed M5.4 identities or a validated
reusable representation.

## Artifact output

Create one dedicated result artifact, without overwriting any prior artifact:

`data/processed/part3_m553_threshold_sensitivity_results.json`

It must contain:

- protocol and threshold list;
- target and stage identifiers;
- exact strategy/semantics version;
- measured metrics;
- derived metrics and formulas;
- candidate-identity provenance;
- runtime, CPU, RSS, and disk observations;
- threshold-250 consistency checks;
- whether optional thresholds 10/50 were run;
- explicit `experiments_executed` metadata.

Create one focused report:

`part3_m553_threshold_sensitivity_report.md`

The report must distinguish already measured standalone rows from newly
measured cumulative identity results. It must not select, rank, recommend, or
label any threshold or architecture as best, optimal, preferred, or final.

## Resource budget and stopping criteria

### Expected scale

Existing standalone evidence shows that number/combination candidate counts
rise sharply toward threshold 250, while the threshold-250 cumulative unions
contain approximately 48 million candidates per target. Lower standalone
thresholds are much smaller, but cumulative M4 ∪ M5.2 identities remain the
dominant baseline. These are planning references, not predictions of
cumulative results.

The observed M5.4 peak RSS of approximately 7.2 GB is a reference envelope,
not a guaranteed limit. M5.3.3 and M5.3.4 standalone runs were approximately
3.6–3.7 GB RSS, but cumulative identity unions can require more memory.

### Required controls

- Process one target source at a time: complete S2 validation and release
  temporary structures before S3.
- Use Python 3.11.
- Reuse normalized source data and reusable indexes where safe.
- Retain only the candidate maps needed for the current marginal comparison.
- Stream or compactly represent identities where the existing implementation
  permits; never retain redundant copies.
- Never construct the full Source-1 × target Cartesian product.
- Record wall time, CPU time, peak RSS, and disk usage for every target/run.

### Stop before completion if any condition occurs

- RSS approaches the observed 7.2 GB reference and continues rising;
- available disk space falls unexpectedly or artifact growth becomes abnormal;
- runtime is materially beyond the validated threshold-250 cumulative scale;
- candidate-map duplication or identity retention becomes unsafe;
- any semantic mismatch, missing validation universe, or threshold-250
  consistency failure is detected.

If stopped, preserve diagnostics and report the incomplete threshold/target;
do not silently reduce semantics, cap candidates, or substitute aggregate
recall.

## Decision criteria, not architecture decisions

The results should enable later analysis using measurable quantities:

- additional marginal pair recall and complete-entity recall;
- marginal candidate cost;
- percentage of previously missed pairs recovered;
- candidate growth;
- P95/P99/maximum tail increase;
- zero-candidate entity change;
- measured blocking runtime, CPU, RSS, and disk.

“Materially useful” must be defined after observing the approved baseline
scale, for example as a pre-registered threshold-specific improvement in
incremental recovery that remains acceptable under candidate-cost and
tail-risk limits. This design deliberately does not choose those limits or
select a winning threshold/architecture.

## Open uncertainties

- Lower-threshold cumulative overlap with M4 and M5.2 is unmeasured.
- The standalone threshold curves do not predict cumulative marginal
  recovery.
- M5.3.4 may remain fully overlapped at lower thresholds, but this requires
  actual identity-union measurements.
- The four-point primary sweep may or may not require 10/50 refinement.
- Downstream matcher performance is not measured by this experiment design.
