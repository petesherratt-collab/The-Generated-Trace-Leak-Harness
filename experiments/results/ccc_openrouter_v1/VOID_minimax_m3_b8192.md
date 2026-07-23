# VOID — MiniMax M3 1,024/8,192 budget diagnostic

Date: 2026-07-21  
Prefix: `ccc_openrouter_v1_minimax_m3_b8192`  
Status: void for inference; never resume or pool

The run was stopped after 159 arithmetic rows and before code or SQL. It contains
153 parsed scores, six `truncated_no_score` failures, 23 retrying cells, and 17
retry recoveries. Every failure exhausted the 8,192-token retry.

All failures were in answer-only:

- correct candidate: 4 failures;
- wrong-matching candidate: 2 failures;
- no-injection baseline: 0 failures observed.

After the third answer-only/correct failure, that 48-cell primary stratum could no
longer meet the five-percentage-point balance gate even if every remaining cell
succeeded: 3/48 is 6.25%. Five injected failures likewise exceeded a five-point
injected-versus-baseline truncation difference. Two in-flight calls settled during
termination, producing the final six-failure count above.

Recorded attempt cost was $0.212743. Per Amendment 5, MiniMax is deferred pending
a separately validated structured-output protocol; this namespace is excluded.
