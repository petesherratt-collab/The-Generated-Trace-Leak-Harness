# Findings — relational (SQL) CCC replication, Stage 2: architectures (preregistered)

**Run:** 2026-07-17, operator's machine (CPython 3.13.14, SQLite 3.50.4, concurrent 6-worker
single writer; ~55 min) · **Prereg:** [`../PREREG_ccc_sql.md`](../PREREG_ccc_sql.md) ·
**Adapter:** `run_ccc_sql_stage2.py` · **Seed:** `838271906` · all 5 models admitted (Stage-1
universal capture) · 24 items × 5 × 4 architectures × 2 mirrored refs × 2 candidates × 3 reps
= 5,760 judge cells + 360 router solves ·
**Evidence:** [`ccc_sql_obs_stage2.jsonl`](ccc_sql_obs_stage2.jsonl),
[`ccc_sql_solver_stage2.jsonl`](ccc_sql_solver_stage2.jsonl),
[`ccc_sql_prompts_stage2.jsonl`](ccc_sql_prompts_stage2.jsonl),
[`ccc_sql_meta_stage2.json`](ccc_sql_meta_stage2.json)

## Headline

In the relational domain — where capture is universal and extreme — **context isolation and
conflict routing both recover discrimination for all five models, isolation with a byte-level
guarantee. Written verification reduces capture but does not eliminate it (large residuals
remain for deepseek and llama).** The safeguard ordering from the prior domains holds:
**isolation (structural) ≥ router ≫ written verification (partial).**

## Integrity audit (independently re-verified)

- **5,760 rows = 5,760 unique cells**; max 1 attempt; **0 duplicate successes**; 0 out-of-range;
  5,747 successes / 13 failures retained.
- **0 order_index↔cell mismatches** under 6-way concurrency; 288 distinct prompts all resolve.
- **Isolation byte-invariant: 720/720 pairs identical** (24×5×2×3), independently recomputed.
- 360 router solves, **334 parseable** (26 unparseable → fail-safe quarantine); solver dedup 0.
- Metadata: seed `838271906`, SQLite 3.50.4, **gold signature matched** (version gate).
- All contrasts recomputed independently from raw scores; matched the adapter.

## Missingness (fail-closed): 13 failures, gemini + llama verify_written (as in every run); one
llama isolation and one llama score-only cell. gemini verify mitigation n=22, llama n=20-23.

## The capture is a genuine reversal (per-arm mean discrimination, contaminated score-only)

| Model | correct reference | wrong reference | susceptibility |
|---|---:|---:|---:|
| gpt-4o-mini | +94.4 | **−75.0** | +169.4 |
| claude-haiku-4.5 | +100.0 | **−50.0** | +150.0 |
| gemini-2.5-flash | +100.0 | **−83.3** | +183.3 |
| deepseek-chat | +99.3 | **−71.5** | +170.8 |
| llama-3.3-70b | +100.0 | **−61.1** | +159.4 |

With a *correct* reference the judge is near-perfect; with a *wrong* one it flips to scoring the
wrong candidate above the correct — the same reversal Stage 1 showed, now as a causal
mirrored-reference contrast. All susceptibilities supported (n=23–24).

## Preregistered safeguard scorecard (all supported; but read residuals, not just deltas)

| Contrast (predicted > 0) | gpt | claude | gemini | deepseek | llama |
|---|---:|---:|---:|---:|---:|
| Isolation gain (wrong ref) | **+106.6 ✅** | **+104.2 ✅** | **+123.9 ✅** | **+137.5 ✅** | **+110.1 ✅** |
| Router gain (wrong ref) | **+167.5 ✅** | **+150.0 ✅** | **+183.3 ✅** | **+165.4 ✅** | **+152.6 ✅** |
| Router detection (pp) | **+84.7 ✅** | **+100.0 ✅** | **+59.7 ✅** | **+91.7 ✅** | **+90.3 ✅** |
| Verification mitigation (Δ) | +162.5 ✅ | +136.1 ✅ | +182.6 ✅ | +119.9 ✅ | +104.3 ✅ |

### Why the verification delta is misleading — the residual is the honest number

The mitigation Δ = susceptibility(score_only) − susceptibility(verify_written) is huge only
because the score-only baseline is huge. The number that matters is the **residual capture
still present under written verification**:

| Model | residual susceptibility under verify_written | verdict |
|---|---:|---|
| gpt-4o-mini | +6.9 [+1.0, +12.0] | small residual remains (supported) |
| claude-haiku-4.5 | +13.9 [+0.2, +33.8] | residual remains (supported) |
| gemini-2.5-flash | −0.8 [−6.6, +5.0] | fully rescued (only model) |
| deepseek-chat | **+50.9 [+34.0, +67.9]** | large residual remains |
| llama-3.3-70b | **+56.2 [+32.0, +83.9]** | large residual remains |

**Written verification is a partial safeguard here too**, not a fix: 4 of 5 models retain
supported residual capture, two of them large. This is fully consistent with the numeric and
code findings — SQL does **not** overturn "prompt-level verification is incomplete."

## Isolation restores to reference-neutrality (structural, byte-audited)

Under `context_isolated_score_only` the discrimination gap between correct- and wrong-reference
runs is **≈ 0 for every model** (gpt −4.5, claude +0.00, gemini +0.7, deepseek −8.7, llama +2.3;
all CIs include 0). Because those prompt pairs are byte-identical, any residual is pure sampling
noise — the reference provably cannot act. Isolation lifts wrong-reference discrimination from
−50…−83 back to +32…+66 (clean-baseline level). This is the one safeguard whose guarantee is
structural, not behavioural.

## Router: recovers fully, detection strong

Router gain ≈ susceptibility for every model (+150 to +183): routing wrong-reference cases to
quarantine + verify restores discrimination. Detection is +60 to +100pp (gemini lowest at +60 —
its solver parsed slightly less cleanly). The router's mechanical comparator — the frozen SQL
canonicalizer applied to the solver's answer and the reference — handled relational
result-equivalence without incident (334/360 clean solves; the rest fail-safe to quarantine).
This is the domain where the router is strongest, because comparing a canonical query result is
exactly what a mechanical comparator does best.

## What SQL adds to the three-domain story

1. **Capture and its severity are domain-dependent** — relational is universal and ~2× the
   magnitude of arithmetic/code; deepseek (robust in code) is among the most captured.
2. **Safeguard *efficacy* is also domain-dependent, but with one invariant**: isolation holds
   structurally in every domain (byte-audited); the router holds where mechanical comparison is
   clean (strongest here); written verification is partial everywhere and never a complete fix —
   confirmed by the residual analysis, not the delta.
3. The only universal, guarantee-backed recommendation across all three domains remains: **keep
   the foreign conclusion out of the judge's context.**

## Release-gate check (all applicable gates passed)

1. ✅ Items hash + gold signature matched on SQLite 3.50.4; self_verify passed; CPython in set.
2. ✅ Single writer; no malformed/duplicate-success rows.
3. ✅ **Isolation byte-invariant 720/720.**
4. ✅ Missingness reported before estimates; factor-correlated missingness disclosed.

## Non-claims and caveats

- 24 hand-authored SQLite tasks; no claim about SQL benchmarks or production database agents.
- "Verification mitigation supported for all" is a delta artifact of an extreme baseline; the
  residual analysis is the load-bearing result and shows verification remains incomplete.
- Router *detection* (a routing-rate contrast) being supported does not by itself prove end-to-end
  safety; the router *gain* (recovered discrimination) is the outcome that does, and it is
  supported here for all five.
- Scores are coarse (0/100 saturation); the reversal and the isolation neutrality are established
  by decomposition, not point magnitudes alone.
