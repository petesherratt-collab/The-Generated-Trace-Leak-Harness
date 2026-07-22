# VOID — GLM 5.2 bounded score-only run

Date: 2026-07-21  
Prefix: `ccc_openrouter_v1_glm52_bounded`  
Status: void for inference; never resume or pool

The run was stopped during arithmetic and before code or SQL. Eight in-flight
responses settled during termination, producing the final diagnostic counts:

- 225 arithmetic rows;
- 219 parsed scores and six `truncated_no_score` failures;
- 41 cells used the 2,048-token retry;
- failures: answer-only/correct 2, answer-only/wrong 3,
  full-rationale/wrong 1, baseline 0;
- recorded attempt cost: $0.591687.

The answer-only/wrong primary stratum has at least 3/48 = 6.25% missingness, and
injected primary truncation is at least 5/96 = 5.21% versus zero observed baseline
truncation. Both exceed the preregistered five-point balance rule. The namespace is
therefore unmeasurable and excluded under Amendment 8.
