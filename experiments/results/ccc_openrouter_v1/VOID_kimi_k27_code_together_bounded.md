# VOID — Kimi K2.7 Code bounded score-only run

Date: 2026-07-22  
Prefix: `ccc_openrouter_v1_kimi_k27_code_together_bounded`  
Status: void for inference; never resume or pool

The run was stopped during arithmetic and before code or SQL. Four in-flight rows
settled during termination, producing:

- 37 arithmetic rows;
- 28 parsed scores and nine `truncated_no_score` failures;
- 16 cells used the 2,048-token retry;
- failures: no-injection/correct 3, answer-only/correct 2,
  answer-only/wrong 1, full-rationale/correct 1,
  full-rationale/wrong 1, solver-rationale/correct 1;
- recorded attempt cost: $0.221774.

The no-injection/correct primary stratum has at least 3/48 = 6.25% missingness,
exceeding the preregistered five-point balance rule. The namespace is unmeasurable
and excluded under Amendment 9.
