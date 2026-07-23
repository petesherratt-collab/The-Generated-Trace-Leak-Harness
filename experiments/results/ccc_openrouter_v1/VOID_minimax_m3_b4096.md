# VOID — MiniMax M3 1,024/4,096 budget diagnostic

Date: 2026-07-21  
Prefix: `ccc_openrouter_v1_minimax_m3_b4096`  
Status: void for inference; never resume or pool

The complete arithmetic domain contains 384 cells: 367 parsed scores and 17
`truncated_no_score` failures. All failures exhausted both the 1,024-token primary
attempt and the 4,096-token retry.

Primary-stratum completion:

| Condition | Candidate | Parsed / expected | Completion |
|---|---|---:|---:|
| no injection | correct | 46 / 48 | 95.8% |
| no injection | wrong matching | 48 / 48 | 100.0% |
| answer only | correct | 43 / 48 | 89.6% |
| answer only | wrong matching | 44 / 48 | 91.7% |

The maximum primary completion gap is 10.4 percentage points, exceeding the
preregistered five-point limit. Injected primary truncation is 9/96 (9.4%) versus
baseline truncation of 2/96 (2.1%), a 7.3-point difference. The result is therefore
not condition-balanced and cannot support a CCC estimate.

The launcher entered code before termination was observed; its 15 successful code
cells are part of this same void namespace and are also excluded. Recorded attempt
cost was $0.455806 for arithmetic plus $0.014927 for code, or $0.470733 total.

Per Amendment 4 of `experiments/PREREG_ccc_openrouter_panel.md`, the replacement
MiniMax block starts from zero under prefix `ccc_openrouter_v1_minimax_m3_b8192`
with a 1,024-token primary ceiling and 8,192-token retry ceiling.
