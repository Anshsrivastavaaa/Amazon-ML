# M5.5.4 Architecture-Hypothesis Comparison

## Scope and neutrality

This is an analysis-only checkpoint. No candidate sets were generated, no
blocking implementation was changed, and no M5.3 experiment was rerun.
The machine-readable comparison is
[part3_m554_architecture_hypotheses.json](data/processed/part3_m554_architecture_hypotheses.json).

Thresholds 5, 25, and 250 have measured cumulative evidence. Thresholds 10,
50, and 100 were **not** cumulatively evaluated. No further threshold
experiments were authorized after threshold 25.

The comparison describes measured support, resource implications, unknowns,
assumptions, and future validation needs. It does not rank, select, or
recommend an architecture.

## Evidence provenance

- M5.4 cumulative threshold-250 artifacts and report;
- M5.5.1 normalized evidence, commit `3aecf47`;
- M5.5.2 resource/cost model, commit `71befb2`;
- threshold-5 cumulative evidence, commit `4b8964d`;
- threshold-25 resource-stop evidence, commit `73a6f1e`;
- standalone M5.3/M5.3.4 threshold rows where explicitly identified.

All cumulative unions use actual per-S1 candidate identities. Standalone
recall is not used to infer cumulative overlap.

## S2 measured cumulative evidence

| Concept / measured stage | Pair recall | Entity recall | Candidate pairs | Avg/S1 | P95 | P99 | Max | Zero S1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 only | 0.389827 | 0.427555 | 14,999,941 | 33.985 | 168 | 249 | 684 | 240,031 |
| M4 ∪ M5.2 | 0.677909 | 0.679583 | 39,196,644 | 88.808 | 296 | 434 | 1,115 | 111,444 |
| M4 ∪ M5.2 ∪ M5.3.3(5) | 0.680542 | 0.681991 | 39,207,683 | 88.833 | 296 | 434 | 1,115 | 110,009 |
| M4 ∪ M5.2 ∪ M5.3.3(25) | 0.688069 | 0.688344 | 39,380,227 | 89.224 | 297 | 435 | 1,115 | 106,236 |
| M4 ∪ M5.2 ∪ M5.3.3(250) | 0.733469 | 0.727432 | 48,053,985 | 108.876 | 328 | 458 | 1,115 | 82,780 |
| Full union with M5.3.4(5/25/250) | same as preceding stage | same | same at each measured threshold | same | same | same | same | same |

M5.3.3 marginal additions after M4 ∪ M5.2 were:

- threshold 5: `1,946` pairs, `1,063` entities, `11,039` candidates,
  candidate cost `5.673`;
- threshold 25: `7,511` pairs, `3,867` entities, `183,583` candidates,
  candidate cost `24.442`;
- threshold 250: `41,075` pairs, `21,119` entities, `8,857,341`
  candidates, candidate cost `215.638`.

## S3 measured cumulative evidence

| Concept / measured stage | Pair recall | Entity recall | Candidate pairs | Avg/S1 | P95 | P99 | Max | Zero S1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M4 only | 0.382646 | 0.410579 | 15,029,807 | 34.053 | 168 | 249 | 724 | 242,191 |
| M4 ∪ M5.2 | 0.659335 | 0.651615 | 39,106,086 | 88.603 | 296 | 434 | 1,115 | 111,968 |
| M4 ∪ M5.2 ∪ M5.3.3(5) | 0.662014 | 0.654098 | 39,116,510 | 88.626 | 296 | 434 | 1,115 | 110,504 |
| M4 ∪ M5.2 ∪ M5.3.3(25) | 0.669517 | 0.660533 | 39,284,812 | 89.008 | 296 | 434 | 1,115 | 106,782 |
| M4 ∪ M5.2 ∪ M5.3.3(250) | 0.715141 | 0.700434 | 47,725,936 | 108.133 | 327 | 457 | 1,115 | 83,737 |
| Full union with M5.3.4(5/25/250) | same as preceding stage | same | same at each measured threshold | same | same | same | same | same |

M5.3.3 marginal additions after M4 ∪ M5.2 were:

- threshold 5: `2,115` pairs, `1,096` entities, `10,424` candidates,
  candidate cost `4.929`;
- threshold 25: `8,038` pairs, `3,936` entities, `178,726` candidates,
  candidate cost `22.235`;
- threshold 250: `44,056` pairs, `21,547` entities, `8,619,850`
  candidates, candidate cost `195.657`.

## Architecture-hypothesis matrix

The following concepts are compared without ordering them.

| Concept | Measured support | Candidate/resource implications | Unknowns and assumptions | Future validation |
|---|---|---|---|---|
| M4 only | Baseline recall and candidate distribution measured for S2/S3. | Approximately 15.0M candidates per target; lower average and tails than cumulative unions. | Assumes M4 semantics remain unchanged; does not recover pairs missed by M4. | Downstream matcher benchmark and error analysis. |
| M4 ∪ M5.2 | Large measured incremental recovery beyond M4: 212,979 S2 and 218,433 S3 pairs. | Approximately 39.1–39.2M candidates; P99 434 and max 1,115. | Candidate volume may dominate downstream scoring; M5.2 overlap is split-specific. | Measure downstream scoring under actual implementation and memory limits. |
| M4 ∪ M5.2 ∪ M5.3.3 | Incremental recovery measured at 5, 25, and 250. | Threshold 5/25 add relatively small candidate growth; threshold 250 adds approximately 8.6–8.9M candidates. | Thresholds 10/50/100 lack cumulative measurements. | No further threshold runs authorized in M5.5.3; future work would require approval. |
| M4 ∪ M5.2 ∪ M5.3.3 ∪ M5.3.4 | At thresholds 5, 25, and 250, M5.3.4 added zero candidates, pairs, and entities for both targets. | Measured full-union candidate sets equal their preceding M5.3.3 stages at those thresholds; combination generation still contributed runtime during the experiments. | This zero contribution is not generalized to thresholds 10/50/100 or other splits. | Revisit only under a separately approved experiment or downstream error analysis. |
| Threshold-sensitive M5.3.3 variants at 5 and 25 | Both are measured cumulative variants, with threshold-specific recovery/cost values above. | Threshold 25 has more measured recovery and larger candidate growth than threshold 5; threshold 25 also exceeded the prior RSS reference. | These are observations, not universal superiority/inferiority claims. | Downstream model impact and explicit resource budget validation. |
| Optional M5.3.4 inclusion/exclusion | Measured zero incremental candidate contribution at 5, 25, and 250. | Candidate identity volume unchanged in all three measured cumulative comparisons; runtime/resource overhead was still observed during generation. | No evidence exists for untested thresholds or production behavior. | Assess implementation overhead and matcher integration before any policy choice. |

## Threshold sensitivity table

| Target | Threshold | M5.3.3 new pairs | Added candidates | Candidate cost | M5.3.4 new pairs | M5.3.4 added candidates |
|---|---:|---:|---:|---:|---:|---:|
| S2 | 5 | 1,946 | 11,039 | 5.673 | 0 | 0 |
| S2 | 25 | 7,511 | 183,583 | 24.442 | 0 | 0 |
| S2 | 250 | 41,075 | 8,857,341 | 215.638 | 0 | 0 |
| S3 | 5 | 2,115 | 10,424 | 4.929 | 0 | 0 |
| S3 | 25 | 8,038 | 178,726 | 22.235 | 0 | 0 |
| S3 | 250 | 44,056 | 8,619,850 | 195.657 | 0 | 0 |

M5.3.4 produced zero incremental contribution at measured thresholds 5, 25,
and 250 for both S2 and S3. This statement is limited to those measured
thresholds.

## Resource envelope

Measured blocking RSS:

| Evidence | Peak RSS |
|---|---:|
| M5.4 cumulative reference | ~7.23 GB |
| Threshold 5 | 7.62 GB |
| Threshold 25 | 8.44 GB |

Threshold 25 exceeded the previous M5.4 reference. The threshold-25
experiment completed and was captured, but no further threshold execution was
authorized. This measured blocking RSS is not a downstream matcher memory
requirement.

M5.5.2 contains separate hypothetical downstream scoring/memory scenarios.
Those scenarios are estimates based on explicit assumed time-per-candidate
and bytes-per-pair values; they are not measured performance and are not
combined with blocking RSS.

## Evidence gaps and implications for later decisions

- Cumulative thresholds 10, 50, and 100 were not evaluated.
- Threshold 25 exceeded the prior resource reference, limiting further
  sensitivity evidence.
- No downstream matcher benchmark has been run.
- Standalone M5.3 recall cannot establish cumulative complementarity.
- Results are specific to the fixed validation split and approved semantics.
- The evidence does not establish behavior on the competition test set.
- The measured M5.3.4 zero contribution does not establish zero contribution
  at untested thresholds.

Later decision-making should use the measured recall/candidate/resource
quantities, the explicit evidence gaps, and any separately approved
downstream validation. This checkpoint makes no architecture decision.
