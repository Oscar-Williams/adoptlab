# Materials experiment v1

Measured on 2026-09-30 using DeepSeek Flash, temperature 0, thinking disabled, one serial executor. Six synthetic task families, two materials and three correlated trials per task produced 72 episodes. B was fixed before held-out observations.

| Stratum | A | B |
|---|---:|---:|
| All task verdicts | 21/36 | 36/36 |
| Valid artifacts | 21/30 | 30/30 |
| Correct input rejection | 0/6 | 6/6 |

| Family | Split | A | B |
|---|---|---:|---:|
| currency | exploration | 6/6 | 6/6 |
| empty | held_out | 0/6 | 6/6 |
| invalid | held_out | 0/6 | 6/6 |
| threshold | exploration | 5/6 | 6/6 |
| timezone | held_out | 4/6 | 6/6 |
| whitespace | exploration | 6/6 | 6/6 |

## Interpretation

The improved material completed more of these frozen tasks. Empty outputs and invalid inputs accounted for most failures with A. The two variants have identical tool schemas and backend code; descriptions and the onboarding guide change together. This experiment estimates the bundled material effect and does not isolate each wording change.

Usage/reservation-priced cost upper bounds: A ¥0.453938; B ¥0.524712. Peak cache-miss rates conservatively price all input; actual invoice charges may be lower. Unresolved network attempts retain their worst-case reservation.

## Execution efficiency

| Material | Median seconds | Requests | Tool calls | Cost upper bound per success (CNY) |
|---|---:|---:|---:|---:|
| A | 5.562 | 144 | 144 | 0.021616 |
| B | 5.704 | 139 | 138 | 0.014575 |

Cost per success includes failed attempts. Elapsed time includes this local workflow and network conditions; it does not rank competitive platforms. Token counts and requests remain in the private execution traces.

Family-level uncertainty:
```json
{
  "all": {
    "families": 6,
    "mean_difference": 0.4166666666666667,
    "family_bootstrap_95_percentile": [
      0.08333333333333333,
      0.75
    ],
    "interpretation": "Exploratory family resampling with few clusters; not a population guarantee or significance test."
  },
  "exploration": {
    "families": 3,
    "mean_difference": 0.055555555555555546,
    "family_bootstrap_95_percentile": [
      0.0,
      0.16666666666666663
    ],
    "interpretation": "Exploratory family resampling with few clusters; not a population guarantee or significance test."
  },
  "held_out": {
    "families": 3,
    "mean_difference": 0.7777777777777778,
    "family_bootstrap_95_percentile": [
      0.3333333333333333,
      1.0
    ],
    "interpretation": "Exploratory family resampling with few clusters; not a population guarantee or significance test."
  }
}
```

Three held-out families and three trials per task support exploratory comparisons. Trial repetition, a single model, synthetic records and preselected task families limit transfer. This result measures model task performance. Independent human integration, product-market fit, retention and revenue await real user evidence.

Recompute: `python scripts/analyze.py`. Original traces and the frozen protocol remain outside the repository in the local runtime directory. A public report omits credentials, personal paths, subject IDs and free text.
