# Void diagnostic — MiniMax M3 1,024/2,048 budget

Stopped: 2026-07-21, before code or SQL began.

This namespace is diagnostic only and must never be resumed, pooled, or reported
as the CCC estimate:

- prefix: `ccc_openrouter_v1_minimax_m3`
- arithmetic rows: 83 of 384
- successful rows: 77
- failures: 6, all `truncated_no_score`
- failure conditions: answer-only 3, solver-rationale 2, full-rationale 1,
  no-injection 0
- recorded attempt cost: USD 0.094844

Every failed cell exhausted both 1,024 and 2,048 output tokens. The absence of
baseline failures made the partial missingness treatment-skewed. The corrected
MiniMax run starts from zero under `ccc_openrouter_v1_minimax_m3_b4096`, retaining
the 1,024-token primary attempt and increasing only the retry ceiling to 4,096.
