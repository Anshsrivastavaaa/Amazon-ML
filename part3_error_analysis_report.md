# Part 3 — M3.5 Baseline Recall Error Analysis

## Scope

This is a diagnostic checkpoint after the M3 compact-name exact blocking
baseline. It does not implement token, address, postal, character-ngram, or
approximate blocking.

The implementation is in
[`src/part3_error_analysis.py`](./src/part3_error_analysis.py). The structured
artifact is
[`data/processed/part3_error_analysis_results.json`](./data/processed/part3_error_analysis_results.json).

## Method

- Same deterministic 20% Source 1 validation split as M3.
- Validation seed: `42`.
- Validation entities: `441,365`.
- Existing ground truth only; target indexes were built without labels.
- Baseline under analysis: `compact_name`.
- Missed true pairs were sampled independently and deterministically.
- Sample size: `10,000` missed pairs for S1→S2 and `10,000` for S1→S3.
- Diagnostic sampling seed: `20260927`.
- Part 2 representations reused:
  - `name_clean_unicode`
  - `name_nopunct`
  - `address_clean` as conservative `safe_unicode()` output
  - `name_core` as `experimental_suffix_stripped()` output

The category classifier assigns one primary category using a documented
precedence order. Pair-level representation values and diagnostic signals are
retained in the JSON artifact. Recoverability flags are heuristics based on
observed pair evidence; they are not measurements of an unimplemented
candidate-generation strategy. Recoverability flags can overlap.

## Missed-pair totals

| Target | True validation pairs | Missed by compact baseline | Recovered by compact baseline | Sampled missed |
|---|---:|---:|---:|---:|
| S1→S2 | 739,298 | 581,019 | 158,279 | 10,000 |
| S1→S3 | 789,453 | 614,299 | 175,154 | 10,000 |

## Primary miss categories

### S1→S2

| Category | Count | Percentage |
|---|---:|---:|
| Abbreviation variation | 3,231 | 32.31% |
| Legal suffix variation | 2,292 | 22.92% |
| Transliteration / Unicode variation | 1,269 | 12.69% |
| Additional / missing tokens | 1,191 | 11.91% |
| Weak name but address informative | 898 | 8.98% |
| Word-order change | 690 | 6.90% |
| Typo / spelling variation | 353 | 3.53% |
| Exact normalized-name mismatch | 42 | 0.42% |
| Missing / empty address | 23 | 0.23% |
| Partial / truncated name | 11 | 0.11% |
| Very short name | 0 | 0.00% |
| Other / unknown | 0 | 0.00% |

### S1→S3

| Category | Count | Percentage |
|---|---:|---:|
| Abbreviation variation | 3,309 | 33.09% |
| Legal suffix variation | 2,061 | 20.61% |
| Additional / missing tokens | 1,794 | 17.94% |
| Weak name but address informative | 945 | 9.45% |
| Transliteration / Unicode variation | 733 | 7.33% |
| Word-order change | 634 | 6.34% |
| Typo / spelling variation | 389 | 3.89% |
| Exact normalized-name mismatch | 98 | 0.98% |
| Missing / empty address | 25 | 0.25% |
| Partial / truncated name | 12 | 0.12% |
| Very short name | 0 | 0.00% |
| Other / unknown | 0 | 0.00% |

The dominant problem is not random short-name ambiguity. It is variation in
abbreviations, legal suffixes, token composition, and ordering. “Very short
name” did not appear in either diagnostic sample under the configured
thresholds.

## Diagnostic recoverability signals

| Target | Token evidence | Address evidence | Approximate-name evidence | Difficult by these signals |
|---|---:|---:|---:|---:|
| S1→S2 | 6,979 (69.79%) | 9,123 (91.23%) | 654 (6.54%) | 141 (1.41%) |
| S1→S3 | 7,352 (73.52%) | 8,631 (86.31%) | 688 (6.88%) | 196 (1.96%) |

These are overlapping flags. For example, a pair can have both token and
address evidence. The results suggest that token and address-derived
strategies should be evaluated before approximate retrieval. Approximate
evidence is a minority signal in this sample, while address evidence is
especially common.

## Missed versus recovered distributions

### Name length

| Target/group | Mean | Median | P95 | P99 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| S2 missed | 24.147 | 24 | 36 | 42 | 3 | 59 |
| S2 recovered | 21.968 | 21 | 35 | 41 | 3 | 63 |
| S3 missed | 24.036 | 24 | 36 | 41 | 4 | 64 |
| S3 recovered | 22.205 | 22 | 36 | 42 | 3 | 60 |

### Token counts

| Target/group | 1 token | 2 | 3 | 4 | 5 | 6+ |
|---|---:|---:|---:|---:|---:|---:|
| S2 missed | 51 | 1,142 | 3,064 | 4,382 | 1,119 | 242 |
| S2 recovered | 125 | 2,324 | 2,903 | 3,436 | 943 | 269 |
| S3 missed | 41 | 1,201 | 3,031 | 4,274 | 1,189 | 264 |
| S3 recovered | 150 | 2,177 | 2,980 | 3,474 | 968 | 251 |

All sampled pairs had a non-empty Source 1 address after conservative
normalization. Address availability therefore does not explain these sampled
misses; address content and formatting differences remain useful signals.

### Country

| Target/group | US | India |
|---|---:|---:|
| S2 missed | 5,687 (56.87%) | 4,313 (43.13%) |
| S2 recovered | 7,250 (72.50%) | 2,750 (27.50%) |
| S3 missed | 5,722 (57.22%) | 4,278 (42.78%) |
| S3 recovered | 6,951 (69.51%) | 3,049 (30.49%) |

Misses are disproportionately represented by India relative to recovered
pairs. Country remains an experimental signal, not an exclusion rule.

## Representative examples

Examples below are real validation pairs from the sampled diagnostic artifact.

| Target | Category | Source 1 name | True target name |
|---|---|---|---|
| S2 | Word order | `Primary Care Associates Inc` | `(Inc) Primary Care Associates` |
| S2 | Additional token | `Red Nails` | `Red Nails LP` |
| S2 | Abbreviation | `SHX Properties Pvt. Ltd.` | `shxproperties.com` |
| S2 | Legal suffix | `V S & C Willow Inc` | `V S + C Willow` |
| S2 | Unicode/transliteration | `Lotus Builders Private Limited` | `???? ???????? ???????? ???????` |
| S2 | Weak name/address informative | `Durga Bio Private Limited` | `Durga Bi0 Private` |
| S3 | Word order | `Zimmerman, Baker & Velez LLC` | `LLC Zimmerman, Baker & Velez` |
| S3 | Additional token | `Cultural Guild LLC` | `Dovatavo d/b/a Cultural Guild LLC` |
| S3 | Abbreviation | `Irvin Pharmaceutical Inc` | `Inc Irvin Paermaoceutial` |
| S3 | Legal suffix | `Chromepet Services` | `Chromepet Services Ltd` |
| S3 | Unicode/transliteration | `White Construction Pvt Ltd` | `??????? ??????????? ???????? ???????` |
| S3 | Weak name/address informative | `Garage (India) Link Private Limited` | `garageindialink.com` |

Question marks in the rendered examples reflect source values that could not
be represented by the Windows console encoding; the JSON artifact preserves
the original Unicode values.

## M3.5 conclusion

The compact exact-name baseline misses mostly structured variation that is
likely addressable through token and address-derived candidate passes. Legal
suffix stripping and country-constrained exact matching should not be treated
as sufficient: suffix variation remains common, and country mismatch must not
discard candidates. Approximate retrieval should remain deferred until token
and address experiments quantify any remaining recall gap.

No M4/M5 blocking strategy was implemented in this checkpoint.
