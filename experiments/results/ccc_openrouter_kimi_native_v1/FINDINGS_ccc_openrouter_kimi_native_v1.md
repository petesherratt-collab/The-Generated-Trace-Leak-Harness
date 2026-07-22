# CCC Kimi native-reasoning full run v1

Status: **complete, preregistered full inferential arm**

Kimi K2.7 Code shows strong Contextual Conclusion Capture in SQL under its
native-reasoning protocol, but no capture in arithmetic or code. All 1,344
scheduled cells completed, so every domain passes the preregistered completeness
and missingness safeguards.

## Primary results

| Domain | Bare-conclusion harm | 95% CI | Items | Verdict | Provenance increment | Rationale increment |
|---|---:|---:|---:|---|---:|---:|
| Arithmetic | -11.88 | [-22.92, -0.10] | 16 | ns | -3.3 | -0.3 |
| Code | +1.46 | [-3.96, +8.23] | 16 | ns | -5.1 | -5.8 |
| SQL | **+70.69** | **[+50.00, +91.67]** | 24 | **SUPPORTED** | **+84.7** | +13.9 |

The arithmetic estimate is significantly opposite to the preregistered harm
direction: answer-only injection improved discrimination by 11.88 points relative
to baseline. It is therefore not CCC support. Code is close to zero and uncertain.

SQL is qualitatively different. The +70.69-point harm is large, its lower
confidence bound is +50, and the +84.7 provenance increment identifies source-like
context as the dominant mechanism. Kimi therefore independently reproduces the
study's central pattern that SQL judging is especially capture-prone.

## Completeness and endpoint integrity

- Scheduled and successful cells: 1,344/1,344
- Unique cells: 1,344; duplicates: 0
- Final failures: 0
- Exact one-field JSON and terminal-contract passes: 1,344/1,344
- Final `finish_reason=stop`: 1,344/1,344
- Judge attempts: 1,346; transport attempts: 1,348
- Resolved identity: Kimi K2.7 Code / Together on every provider response
- Prompt records: 448; every SHA-256 verified and every observation reference found
- Completion, truncation, and content-filter balance gaps: 0.0% in every domain

Two arithmetic/full-rationale/correct cells needed the preregistered judge retry.
Their first provider responses ended with `finish_reason=error` and no accepted
score. Both 32,768-token retries returned exact JSON with `stop`; one retry also
recovered from two internal HTTP 503 transport attempts. These events produced no
missing cell and no treatment-control imbalance.

## Reasoning use and cost

| Domain | Cells | Max reasoning tokens | Scored cost |
|---|---:|---:|---:|
| Arithmetic | 384 | 13,517 | $2.76744998 |
| Code | 384 | 13,021 | $1.74185520 |
| SQL | 576 | 11,020 | $1.37145110 |
| **Total** | **1,344** | **13,517** | **$5.88075628** |

The run-internal preflight cost $0.00018510, and the separate launch preflight cost
$0.00018510. Total full-run-path spend was therefore **$5.88112648**. This is close
to the preregistered order of magnitude and far below the earlier frontier-panel
cost.

## Interpretation boundary

This is valid inferential evidence for Kimi under the separately preregistered
native-reasoning protocol: provider-default reasoning, 16,384/32,768 output
headroom, serial execution, and terminal JSON plus normal-stop acceptance. It must
not be pooled as if its response-generation protocol were identical to the terse-
score MiniMax, GLM, or Qwen arms.

Within that boundary, the result is unusually clean: Kimi is not generally
suggestible across domains, but it is extremely capture-prone in SQL. The model's
media prominence does not weaken the finding; including it adds an important
open-weight replication of the SQL-specific effect.
