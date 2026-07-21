# Findings — frontier CCC Phase 2 (`verify_written`)

**Run:** `ccc_frontier_p2` · seed `305774821` · instrument commit `a57e85a` · verify budgets 2048/4096
· 2,496 cells across the 5 conditionally-admitted (domain, judge) pairs. Preregistration:
[`../PREREG_ccc_frontier_phase2.md`](../PREREG_ccc_frontier_phase2.md). Audit (independent
implementation, matches the runner): [`ccc_frontier_p2_audit.txt`](ccc_frontier_p2_audit.txt).

**Question:** does instructing the frontier judge to verify/re-derive in writing before scoring
eliminate the Phase-1 capture? Read from the **residual** bare-conclusion harm *under*
`verify_written` (not the mitigation delta).

## Result: written verification is not a reliable fix

| domain | judge | Phase 1 (score_only) | **Phase 2 residual** | mitigation Δ | verdict |
|---|---|---|---|---|---|
| arith | fable | +62.9 | **+19.4** [+1.5, +39.4] | ~+43 | **capture persists** |
| code | gpt-5.6-sol | +11.2 | **+8.1** [+3.0, +15.9] | ~+3 | **capture persists** |
| SQL | gpt-5.6-sol | +50.6 | **−0.1** [−0.4, +0.0] | ~+51 | **residual ~0** (bounded, not proven) |
| SQL | grok-4.5 | +27.4 | +9.5 [−0.2, +22.2] | ~+18 | residual **uncertain** (CI spans 0) |
| SQL | gemini-3.1-pro | +40.9 | (+6.1, injection-skewed) | — | **unmeasurable** (truncation) |

Of the four **measurable** (judge, domain) cells, `verify_written` eliminated capture in **only one**
— gpt in SQL, where +50.6 collapsed to a residual indistinguishable from zero. Elsewhere a real
residual survived (**fable-arith +19**, **gpt-code +8**, both 95% CIs excluding 0), or was too
uncertain to call (**grok-SQL +9.5**, CI spanning 0). The mitigation is as **model- and
domain-specific as the capture itself**: even within gpt, verification worked in SQL but barely moved
code (+11.2 → +8.1).

## Discipline applied

- **gpt-SQL "eliminated" is bounded, not proven.** −0.1 [−0.4, +0.0] (n=24, full) is about as clean as
  an elimination looks, but a zero-covering CI bounds the residual rather than proving it is zero.
- **gemini-SQL is unmeasurable, not "residual ~0."** Its 10 missing cells are all injection-side
  (`*INJECTION-SKEWED`), tagged **`truncated_no_score`** — under `verify_written` gemini's long written
  derivations exceed the 2048/4096 budget, more often on the harder injected items. Treated as
  unmeasurable under the preregistered condition-balanced safeguard; a larger verify budget might
  recover it (not run — cost).
- **grok-SQL** point estimate +9.5 with upper bound +22 is *not* a clean elimination; reported as an
  uncertain residual, not "verification worked."

## Data quality

- Structural: 0 duplicate cells across all three files; independent recompute matches the runner.
- Missingness: arith 5 (all `worker:HTTPError 402 Payment Required` — transient billing, non-systematic,
  base 3 / inj 2, not skewed), code 0, SQL 10 (all gemini truncation, above). No content filtering
  occurred in Phase 2 (unlike Phase 1 Fable) because Fable is admitted only for arithmetic, where its
  filter stays quiet.

## Conclusion (for the manuscript)

In-context **"verify first" does not dependably remove Contextual Conclusion Capture at the frontier
tier.** It fully worked in 1 of 4 measurable cells; elsewhere the capture persisted, was uncertain, or
the verification's own length made the cell unmeasurable. This supports the study's thesis that
in-context mitigations are fragile and that the reliable safeguard is **structural context isolation**
(byte-audited in the small-tier Stage 2), not asking the same conflicted judge to check its work.
