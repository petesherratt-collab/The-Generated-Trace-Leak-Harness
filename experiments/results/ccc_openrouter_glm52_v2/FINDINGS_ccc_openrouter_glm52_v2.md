# CCC GLM 5.2 full run v2

Status: **complete, preregistered full inferential arm**

GLM 5.2 shows Contextual Conclusion Capture in arithmetic and SQL under the
frozen terse-score protocol. Code has a positive point estimate, but its
confidence interval crosses zero and therefore does not meet the confirmatory
criterion.

## Primary results

| Domain | Bare-conclusion harm | 95% CI | Items | Verdict | Provenance increment | Rationale increment |
|---|---:|---:|---:|---|---:|---:|
| Arithmetic | **+52.08** | **[+25.00, +80.21]** | 16 | **SUPPORTED** | -13.5 | -16.7 |
| Code | +13.33 | [-10.21, +38.33] | 16 | ns | **+52.1** | -4.2 |
| SQL | **+148.61** | **[+129.17, +166.67]** | 24 | **SUPPORTED** | +23.6 | -8.3 |

SQL is again the largest and most certain effect. Arithmetic also shows a large
bare-conclusion effect. In code, answer-only harm is uncertain, but provenance
adds 52.1 points; that secondary contrast suggests source-like framing may matter
even though the preregistered primary code result is not supported.

## Completeness and endpoint integrity

- Scheduled and successful cells: 1,344/1,344
- Unique cells: 1,344; duplicates: 0
- Final failures, judge retries, and transport retries: 0
- Exact one-field JSON and `finish_reason=stop`: 1,344/1,344
- Resolved identity: `z-ai/glm-5.2` / Together on every response
- Prompt records: 448; every SHA-256 verified and every reference resolved
- Completion, truncation, and content-filter balance gaps: 0.0% in every domain
- Reasoning telemetry: 1,344/1,344 records, all zero tokens

## Cost

| Domain | Cells | Scored cost |
|---|---:|---:|
| Arithmetic | 384 | $0.11229024 |
| Code | 384 | $0.06692736 |
| SQL | 576 | $0.12117048 |
| **Total scored cells** | **1,344** | **$0.30038808** |

Including the run-internal and separate launch preflights, the full-run-path total
was **$0.30049448**.

## Interpretation boundary

This finding applies to the frozen score-only contract: reasoning disabled and
excluded, 128/256 output ceilings, structured one-field JSON, and fixed Together
routing. It is directly comparable with MiniMax's terse-score arm, while Qwen and
Kimi retain their separately documented reasoning protocols.

Within that boundary, GLM independently strengthens two conclusions: SQL capture
generalizes widely, and arithmetic capture is not unique to Claude Fable.
