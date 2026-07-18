# Findings — relational (SQL) CCC replication, Stage 1 (preregistered)

> Detailed stage record. For the unified write-up of the whole relational replication
> (Stages 1 + 2 as one bounded study), see [`FINDINGS_ccc_sql.md`](FINDINGS_ccc_sql.md).

**Run:** 2026-07-17, operator's machine (CPython 3.13.14, **SQLite 3.50.4**, concurrent
fixed pool of 6, single writer; ~65 min) · **Prereg:** [`../PREREG_ccc_sql.md`](../PREREG_ccc_sql.md)
· **Adapter:** `run_ccc_sql.py` · **Seed:** `838271905` · 24 frozen SQLite items · 5 models
· 4 conditions · 2 candidates · 2 protocols · 3 reps = 5,760 cells ·
**Evidence:** [`ccc_sql_obs_stage1.jsonl`](ccc_sql_obs_stage1.jsonl),
[`ccc_sql_prompts_stage1.jsonl`](ccc_sql_prompts_stage1.jsonl),
[`ccc_sql_meta_stage1.json`](ccc_sql_meta_stage1.json),
[`ccc_sql_stimuli_stage1.json`](ccc_sql_stimuli_stage1.json)

## Headline

**CCC replicates in the relational domain — the strongest and most uniform capture of the
three domains.** The bare-conclusion primary contrast is **supported in all 5 models**, at
**+106 to +153 discrimination points**, versus +39–88 (arithmetic) and +12–44 (code). At this
magnitude the effect is not a loss of discrimination but a **reversal**: the judge scores the
*wrong* result above the correct one when a neutral reference note vouches for it.

## Integrity audit (independently re-verified)

- **5,760 rows = 5,760 unique cells**; max 1 attempt; **0 duplicate successes**; 0 out-of-range
  scores; 5,737 successes (99.6%) / 23 failures, all retained.
- **0 order_index↔cell mismatches** — the frozen schedule order is preserved despite 6-way
  concurrency (each row carries its frozen position; analysis is order-independent).
- 384 distinct prompts (exactly 24×4×2×2), all resolving in the manifest.
- Metadata: seed `838271905`, **SQLite 3.50.4** (≠ the 3.45.1 verified in development), and the
  **frozen gold signature matched** — the fail-closed SQLite-version gate confirmed the local
  runtime produces byte-identical gold before running. Execution recorded as
  `concurrent_fixed_pool_single_writer`, workers 6.
- Primary estimates recomputed independently from raw scores; matched the adapter exactly.

## Missingness (fail-closed, before estimates)

23 failures, factor-correlated as in every prior run: **18 are gemini × verify_written** (worst
cell: solver/full_wrong_rationale × wrong_matching, 12/72), the rest a scattering of llama
verify_written. No score_only failures of consequence (llama 1). Fail-closed: the affected
verify_written contrasts lose a few items; the **primary (score_only) contrast is complete at
n=24/24 for four models and 23/24 for llama.**

## Preregistered scorecard — PRIMARY (bare-conclusion injection harm, score_only)

Supported iff CI excludes 0 and ≥ 18/24 items complete.

| Model | Harm [95% CI] | n | Call |
|---|---:|---:|---|
| gpt-4o-mini | **+112.15 [+94.44, +129.86]** | 24 | **SUPPORTED** |
| claude-haiku-4.5 | **+112.50 [+87.50, +137.50]** | 24 | **SUPPORTED** |
| gemini-2.5-flash | **+124.58 [+95.00, +150.62]** | 24 | **SUPPORTED** |
| deepseek-chat | **+153.25 [+134.03, +172.25]** | 24 | **SUPPORTED** |
| llama-3.3-70b | **+106.59 [+86.30, +126.09]** | 23 | **SUPPORTED** |

## It is a genuine reversal, not saturation (per-arm decomposition, score_only)

| Model | baseline disc | injected disc | correct: base→inj | wrong: base→inj |
|---|---:|---:|---:|---:|
| gpt-4o-mini | +31.6 | **−80.6** | 79.9 → 0.0 | 48.3 → 80.6 |
| claude-haiku-4.5 | +54.2 | **−58.3** | 79.2 → 4.2 | 25.0 → 62.5 |
| gemini-2.5-flash | +41.2 | **−83.3** | 63.5 → 0.0 | 22.3 → 83.3 |
| deepseek-chat | +67.8 | **−85.4** | 92.1 → 2.1 | 24.2 → 87.5 |
| llama-3.3-70b | +41.4 | **−66.7** | 80.6 → 0.0 | 37.3 → 66.7 |

Baseline: correct scored high, wrong low → the judge **can** do the relational task. Under the
bare wrong-result note: the correct candidate collapses toward 0 and the wrong candidate rises
toward the injected value, so discrimination goes **negative** — the judge grades by *agreement
with the reference* rather than by verifying against the data. This rules out a scale/saturation
artifact: the same judges discriminate correctly with no injection.

## What this changes about the cross-domain story

1. **First domain with universal capture.** Arithmetic and code each had a non-supported model
   (deepseek in both, borderline); relational captures **all five**, and by 2–3× the magnitude.
2. **Model-dependence is itself domain-dependent — now decisively.** DeepSeek, *not supported*
   in code (+10.2, CI included 0), is the **most captured** model here (+153.2). Robustness does
   not transfer across domains: a judge cannot be certified once and trusted elsewhere. (This is
   the single most important cross-domain finding, and it directly motivates the benchmark's
   per-release integrity gate.)
3. **Hypothesis (stated as such, not claimed):** capture magnitude appears to track
   *verification difficulty*. Relational answers require mentally executing joins/GROUP BY/NULL
   logic over the rows — harder to independently check than arithmetic or code-tracing — and the
   baseline discriminations here are *lower* than in the other domains, consistent with judges
   leaning harder on the injected result the harder the task is to verify. Testable, not
   asserted.

## Stage-1 capture threshold → conditional Stage-2 subset (frozen at first computation)

> **Admitted: all five** — gpt-4o-mini, claude-haiku-4.5, gemini-2.5-flash, deepseek-chat,
> llama-3.3-70b. (No exclusions; the first domain where every model enters Stage 2.)

Stage 2 (four architectures × mirrored references on all five models): 24 × 5 × 4 × 2 × 2 × 3 =
5,760 judge cells + 360 router solves, seed `838271906`.

## Release-gate check (all applicable gates passed)

1. ✅ Items hash matched; CPython 3.13.14 in accepted set; **gold signature matched on SQLite
   3.50.4** (fail-closed version gate); `self_verify()` passed.
2. ✅ Single writer; no malformed/duplicate-success rows (0 dup successes across 5,760 cells).
3. — (isolation byte-audit is a Stage-2 gate.)
4. ✅ Missingness reported before estimates; factor-correlated missingness disclosed.

Concurrency behaved on live API traffic exactly as it did in the offline stub tests: order
preserved, one writer, dedup intact, missingness fail-closed.

## Non-claims and caveats

- 24 hand-authored SQLite tasks; no claim about SQL benchmarks (Spider/BIRD/WikiSQL), text-to-SQL
  systems, or production database agents. A CI containing zero would not have meant immunity; the
  magnitudes here are large but the domain is a frozen micro-domain.
- The verification-difficulty hypothesis is exploratory and not tested by this design.
- Scores are coarse (0/100 common); the reversal is established by the per-arm decomposition, not
  by point magnitudes alone.
