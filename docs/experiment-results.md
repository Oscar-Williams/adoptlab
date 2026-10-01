# AdoptLab v0.2: guide × tool-description experiment

Recorded 2026-10-01. Twelve synthetic tasks, four material combinations, three repeated model trials. Protocol and model results use separate denominators.

| Material | Guide | Descriptions | Protocol | Model acceptance | Model cost upper bound (CNY) |
|---|---|---|---|---|---|
| AA | A | A | 12/12 | 23/36 | 0.800578 |
| AB | A | B | 12/12 | 35/36 | 0.546328 |
| BA | B | A | 12/12 | 36/36 | 0.536240 |
| BB | B | B | 12/12 | 36/36 | 0.730678 |

The matrix contains 48 protocol executions and 144 model episodes. One AB request failed before a model response; its responder is unknown and its failure remains in the denominator. All recorded responders identify as deepseek-flash. The sum of model cost bounds is 2.613824 CNY; reservations for uncertain requests remain separate ledger entries. These are conservative recorded bounds, with provider invoice charges unverified.

## Split and interpretation

Exploration families: threshold, whitespace, currency. Held-out families: timezone, empty output, invalid input. Each material has 18 episodes per split. Exploration acceptance: AA 17/18; AB, BA, BB 18/18. Held-out acceptance: AA 6/18; AB 17/18; BA and BB 18/18. Materials were frozen before the matrix; no held-out tuning was performed.

Guide main effect: +19.44 percentage points; description main effect: +16.67; interaction: −33.33. Family-cluster bootstrap intervals are exploratory with six synthetic clusters: guide [1.39, 38.89], descriptions [1.39, 33.33], interaction [−66.67, −2.78] percentage points. Repeated trials are correlated. The negative interaction reflects overlap between improvements on this task-acceptance scale.

The public report includes each terminal result, task split, cost bound, material content, execution condition and responder. AA/AB/BA/BB are aliases of frozen material IDs. The public comparison pairs only matching task/trial/mode/cohort/condition and known matching responders. Unknown-responder failures remain visible in the table.

## Reproduce and decide

Run python scripts/run_v02_matrix.py with your own configured credentials, then python scripts/analyze_v02.py. New runs may differ; save their protocol and raw results separately. Protocol mode checks service/contract correctness; model mode examines material effects.

For this bounded task catalog, both guide and description clarification improve acceptance relative to AA. Follow-up decisions require additional tasks, models and developer observations. Saved comparisons and automated feedback/revision checks contribute engineering evidence; observed human adoption remains unmeasured.

See [validation](v02-validation.md), [review and iteration](review-results.md), and [historical v0.1](experiment-results-v1.md).
