# Findings — frontier-model extension of CCC (v3 confirmatory run)

**Run:** `ccc_frontier_v3` · **seed** `305774821` · **instrument commit** `982b97e` · **date**
2026-07-20 · **protocol** `score_only` (Phase 1) · four judges × three domains × 4 conditions ×
2 candidates × 3 reps = 5,376 cells. Preregistration: [`../PREREG_ccc_frontier.md`](../PREREG_ccc_frontier.md)
(Amendments 1–3). Reproduce the numbers: [`../audit_ccc_frontier_v2.py`](../audit_ccc_frontier_v2.py)
retargeted to the `v3` files, or see [`ccc_frontier_v3_audit.txt`](ccc_frontier_v3_audit.txt)
(independent implementation; matches the runner exactly).

This is the **confirmatory** run. Two prior runs (2026-07-19) were void (60/240 truncation); the
v2 run (seed 811529437) was retained as **exploratory only** (dead retry path; non-reproducible
`hash(domain)` schedule). v3 fixes both and adds an `empty/truncated/unparseable/content_filtered`
error taxonomy, reproducible `sha256(domain)` scheduling, and missingness reporting by condition ×
candidate. See PREREG Amendment 3.

## Headline

**Primary contrast:** bare-conclusion harm `D(no_injection) − D(answer_only)`, item-clustered
bootstrap (B = 6,000), fail-closed; **SUPPORTED** iff the 95% interval excludes 0 and ≥ 75% of items
are complete.

| domain | gpt-5.6-sol | gemini-3.1-pro-preview | grok-4.5 | claude-fable-latest |
|---|---|---|---|---|
| **arithmetic** | ns (−7.1) | ns (+0.2) | ns (−0.5) | **SUPPORTED +62.9** [+41.0, +86.2] |
| **code** | **SUPPORTED +11.2** [+4.8, +21.2] | ns (−2.5) | ns (+1.4) | unmeasurable — content-filtered |
| **SQL** | **SUPPORTED +50.6** [+23.2, +81.0] | **SUPPORTED +40.9** [+24.2, +57.6] | **SUPPORTED +27.4** [+9.7, +49.6] | unmeasurable — content-filtered |

1. **SQL capture is robust at the frontier tier.** Three independent frontier judges (OpenAI,
   Google, xAI) all show large, significant bare-conclusion harm in SQL, with **large provenance
   increments** (gpt +88, gemini +74, grok +33) — i.e. a conflicting SQL result in context sharply
   erodes the judge's ability to tell a correct query from a wrong one, and it is *sufficient* on its
   own (bare result), consistent with the CCC thesis.
2. **Code capture is model-specific and weak.** Only **gpt-5.6-sol** shows confirmatory code capture
   (+11.2). Notably, **grok-4.5 code did NOT replicate**: the v2 exploratory run had it borderline
   SUPPORTED (+5.7, lower bound +0.31); under the clean confirmatory instrument it is **ns**
   (+1.4, [−2.5, +5.6]). The borderline v2 signal was fragile — a direct demonstration of why the
   confirmatory replication was necessary.
3. **No arithmetic capture** for the three general-purpose frontier judges.
4. **Claude Fable is the mirror image.** It is the *only* judge captured in **arithmetic** (+62.9,
   strong), yet in **code and SQL** its provider **content filter blocks the judge response whenever
   a wrong conclusion/rationale is injected** — so its discrimination there is unmeasurable (below).

## Claude Fable: content filtering, not capture, in code/SQL

Fable's failures are **provider content-filter blocks** (`finish_reason == "content_filter"` on both
attempts; the larger-budget retry fired and could not help — a filter, not a token limit), and the
blocking is **strongly treatment-correlated**:

| domain | missing @ baseline | missing @ injected | tag | verdict |
|---|---|---|---|---|
| arithmetic | 0 | 0 | — | measurable → **SUPPORTED +62.9** |
| code | 12 | 136 | `content_filtered` ×148 | **unmeasurable** (injection-skewed) |
| SQL | 0 | 27 | `content_filtered` ×27 | **unmeasurable** (injection-skewed) |

Because the blocking is concentrated in the injected conditions, the surviving cells are a biased
subset, so the harm contrast is **unmeasurable** under the preregistered condition-balanced
safeguard — even where nominal n clears the floor. Fable's SQL row computes a nominal SUPPORTED
+4.9, but with 27 injection-side content-filter blocks (`*INJ-SKEW`) it is **reported unmeasurable,
not a +4.9 finding.** This reproduced across three independent runs (v2: 135 code / v2-recheck: 135
code / v3: 148 code), so the filtering is systematic, not stochastic. Interpretation: this is a
property of the `~anthropic/claude-fable-latest` endpoint's safety filtering on injected
wrong-rationale content in code/SQL — it is neither evidence of capture nor of immunity.

## Mechanism (descriptive; SQL, where capture is strong)

- **Provenance increment** `harm(solver) − harm(full)` is large and positive in SQL (gpt +88, gemini
  +74, grok +33): an authoritative "solver" label on the wrong rationale adds substantial further
  harm. **Rationale increment** `harm(full) − harm(answer_only)` is small/negative — the bare wrong
  result already does most of the damage, consistent with "conclusion is sufficient, argument not
  necessary." (These are descriptive; intervals not computed for the increments.)

## Integrity / data quality

- **Structural:** 0 duplicate successful cells; `attempts` logged on all 5,376 rows; exact row
  counts per model; reproducible schedule (`sha256(domain)`); metadata records commit, validated
  aliases, force-flag (False), budgets.
- **Missingness** (fail-closed, never imputed): arith 8, code 154, SQL 30. Of these, 220-ish are
  Fable content-filter blocks (above); **14 cells** (mostly gpt) failed `worker:KeyError: 'choices'`
  — the provider returned a body with no `choices` field (transport hiccup); non-systematic (~0.3%),
  fail-closed. This trimmed gpt-arithmetic to exactly the completeness floor (n = 12) but changed no
  verdict.
- Preflight passed for all four aliases; `--force-models` not used; run completed all 5,376 cells.

## Non-claims / limits

- Four specific endpoints **as of 2026-07-20**; two are moving `-latest` aliases (metadata is
  authoritative). No claim about frontier models in general or any named benchmark.
- Frozen micro-domains (16/16/24 items), coarse 0–100 judges: directions and support calls are the
  result; magnitudes indicative. Domain was observed, not randomized — magnitude differences across
  domains are not attributed causally to domain.
- A CI covering zero is not evidence of immunity; a content-filtered cell is not evidence of either
  capture or resistance.
- `verify_written` (Phase 2) not run; `score_only` is the vulnerable, low-cost protocol.

## Phase 2 — does written verification fix it? (`verify_written`)

A conditionally-admitted Phase 2 ran `verify_written` on the Phase-1-captured pairs (see
[`FINDINGS_ccc_frontier_phase2.md`](FINDINGS_ccc_frontier_phase2.md),
[`../PREREG_ccc_frontier_phase2.md`](../PREREG_ccc_frontier_phase2.md)). Reading the **residual** harm
that remains under verification: it eliminated capture in **only 1 of 4 measurable cells** (gpt-SQL,
+50.6 → residual ~0); the residual **persisted** for fable-arith (+19.4) and gpt-code (+8.1, CIs
exclude 0), was **uncertain** for grok-SQL (+9.5, CI spans 0), and gemini-SQL became **unmeasurable**
(verify_written's long derivations truncated, injection-skewed). Written self-verification is thus an
**unreliable, model- and domain-specific mitigation** — consistent with the study's thesis that the
dependable safeguard is structural context isolation, not asking the conflicted judge to re-check.

## Relation to the small-tier study

The frontier SQL result **replicates the small-tier finding that SQL is the most capture-prone
domain**, now at the frontier tier and across three providers. Capture remains **model- and
domain-dependent**: strong and general in SQL, model-specific and weak in code (only gpt), absent in
arithmetic for the general-purpose judges, and — for the one judge captured in arithmetic (Fable) —
unmeasurable in code/SQL because of provider content filtering. No safeguard (isolation/router) was
tested here; that remains the small-tier Stage-2 result.
