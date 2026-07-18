# Findings — the relational (SQL) CCC replication (unified: Stages 1 + 2)

**One preregistered study, two frozen stages, run 2026-07-17** ·
**Prereg:** [`../PREREG_ccc_sql.md`](../PREREG_ccc_sql.md) ·
Stage records (full detail, audits, per-contrast tables):
[Stage 1 — injection](FINDINGS_ccc_sql_stage1.md) ·
[Stage 2 — architectures](FINDINGS_ccc_sql_stage2.md)

## Scope, stated first

The third computational-reasoning domain after arithmetic and Python code: **finite relational
reasoning over frozen SQLite fixtures**, with the SQLite oracle as **mechanical, non-circular
gold** (no model establishes truth). 24 hand-authored tasks spanning joins, grouping, NULL
semantics, ordering, duplicate rows, subqueries, and boundary predicates; five judge models;
frozen seeds; fail-closed analysis. It licenses claims about *this frozen micro-domain*: not SQL
benchmarks (Spider/BIRD/WikiSQL), text-to-SQL systems, production database agents, or open-ended
judging.

A design-specific integrity guarantee: gold depends on the SQLite library version, so the run
**recomputes the gold signature at start and aborts unless it equals the frozen value**. This
fired usefully in production — the operator's machine ran **SQLite 3.50.4** (developed against
3.45.1), and the gate confirmed byte-identical gold before running.

## The replication in one paragraph

A bare, neutrally-labelled wrong query result placed in a judge's context caused **universal and
extreme capture — supported in all 5 models at +106 to +153 discrimination points** (Stage 1),
roughly twice the arithmetic and code magnitudes. At this strength it is a **reversal**: with a
wrong reference the judge scores the wrong result *above* the correct one. All five models were
admitted to Stage 2, where mirrored correct/wrong references confirmed the effect causally
(+150 to +183 susceptibility) and the safeguards were tested. **Context isolation restores
discrimination to reference-neutrality for all five (byte-audited, gap ≈ 0); the conflict router
fully recovers it for all five (mechanical comparison strongest in this domain); written
verification reduces capture but leaves supported residual capture in 4 of 5 models** — a partial
safeguard, not a fix. The safeguard ordering of the prior domains holds:
**isolation (structural) ≥ router ≫ written verification (partial).**

## Design (both stages under one freeze)

| | Stage 1 — injection | Stage 2 — architectures |
|---|---|---|
| Question | Does a conflicting result capture relational judges? | Do the safeguards fix it? |
| Cells | 5,760 (24×5×4 conditions×2 candidates×2 protocols×3 reps) | 5,760 + 360 router solves (24×5×4 archs×2 refs×2×3) |
| Seed | 838271905 | 838271906 |
| Models | all 5 | **all 5 admitted** (Stage-1 universal capture; no exclusions) |
| Execution | concurrent fixed pool (6), single writer | concurrent fixed pool (6), single writer |
| Success | 5,737 / 5,760 (99.6%) | 5,747 / 5,760 (99.8%); 334/360 solves |

Every integrity invariant was verified offline before the runs and re-verified on the evidence:
one row per cell, max 1 attempt, **0 duplicate successes**, **0 order_index↔cell mismatches under
concurrency**, all prompts resolve, gold signature matched on the run machine's SQLite, and every
contrast recomputed independently from raw scores.

## Factor-correlated missingness (preserved, disclosed, never interpreted as safety)

36 failures across both stages (23 + 13), the familiar factor pattern: **gemini × verify_written
dominates** (18 in Stage 1, 5 in Stage 2), with a scattering of llama verify_written and one each
of llama isolation/score-only. Consequences under the frozen ≥18/24 floor: gemini's verification
contrasts run at n=22; llama's at n=20–23; the **score-only primary was complete at n=23–24 for
all five models**. No missingness was imputed or read as robustness.

## Model-specific results (preserved; no cross-model averaging)

Stage 1 bare-conclusion harm (score-only) and Stage 2 safeguard contrasts:

| Model | S1 harm | S2 susceptibility | isolation gain | router gain | **residual under verify** |
|---|---:|---:|---:|---:|---:|
| gpt-4o-mini | **+112 ✅** | **+169 ✅** | **+107 ✅** | **+168 ✅** | +6.9 (small, supported) |
| claude-haiku-4.5 | **+113 ✅** | **+150 ✅** | **+104 ✅** | **+150 ✅** | +13.9 (supported) |
| gemini-2.5-flash | **+125 ✅** | **+183 ✅** | **+124 ✅** | **+183 ✅** | −0.8 (fully rescued) |
| deepseek-chat | **+153 ✅** | **+171 ✅** | **+138 ✅** | **+165 ✅** | **+50.9 (large)** |
| llama-3.3-70b | **+107 ✅** | **+159 ✅** | **+110 ✅** | **+153 ✅** | **+56.2 (large)** |

Router detection was supported for all five (+60 to +100pp). The **residual column is the
load-bearing verification result**: written verification's mitigation *delta* is large only
because the baseline is extreme; the capture that remains under it is still supported for four of
five models, two of them large. Verification is partial here, as in every domain.

## What the unified relational replication establishes — and what it does not

**Established (within scope):**
1. CCC replicates in relational judging — the **strongest and most uniform** of the three domains
   (all five models, ~2× magnitude, a genuine reversal by per-arm decomposition).
2. **Isolation restores reference-neutrality structurally** (byte-identical isolated prompts;
   correct-vs-wrong-reference gap ≈ 0 for all five).
3. **The router fully recovers discrimination** here — its strongest showing across domains,
   because comparing a canonical query result is what a mechanical comparator does best.
4. **Written verification is partial** — supported residual capture in 4/5 models.

**Not established:** anything beyond the frozen micro-domain; named SQL benchmarks; that
verification "works in SQL" (the delta says mitigation, the residual says incomplete); immunity
for any model.

**Effect sizes are domain- and model-dependent** (relational ≈ 2× code; deepseek robust in code,
among the most captured here). Directions and preregistered support calls are the result;
magnitudes indicative.
