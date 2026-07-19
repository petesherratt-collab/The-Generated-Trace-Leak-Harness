# Preregistration — frontier-model extension of CCC (three domains, frozen items)

**Frozen design date:** 2026-07-18 · **Status:** freeze BEFORE any API call. No OpenRouter
request is made until this file is reviewed and committed, the aliases are validated by the
preflight (§ Models), and the operator confirms the key and cost.
**Adapter:** [`run_ccc_frontier.py`](run_ccc_frontier.py) · **Seed:** `619273400`

This extension tests whether **more capable ("frontier latest") judges** are susceptible to
Contextual Conclusion Capture, across all three previously-tested domains. It directly addresses
the manuscript limitation "cost-tier models only; whether frontier judges are equally susceptible
is untested." Frontier results are their **own data point**: given the study's model-dependence
finding, they neither validate nor invalidate the small-tier runs.

## Frozen items (reused), and why that is correct here

The extension **reuses the exact frozen item sets** of the small-tier runs — arithmetic (16
confirmatory items), code (16 items, unit-test gold), SQL (24 items, SQLite oracle) — rather than a
held-out set. This is a deliberate paired design, not a leakage risk: the models act as **judges,
not task-takers**; a judge scores a candidate against data given *in its context*, and correctness
is set by an executable oracle, not recalled from memory. Item reuse therefore gives a **paired,
within-item small-vs-frontier contrast** (does the frontier judge resist on the *same* item where
its small sibling succumbed) with no memorisation advantage. A held-out matched set is recorded as
a possible later robustness check only.

Frozen artifacts reused (hash/gold checks run at start via each domain's own release gate):
`ccc_code_items.py` + `ccc_code_runner.py`; `ccc_sql_items.py` (+ SQLite gold-signature gate);
the arithmetic confirmatory text cache `provinj_texts_confirmatory.json` (+ overrides), verified
frozen.

## Models (identity frozen; alias validated at run start)

Four frontier flagships, one per provider, supplied as exact OpenRouter aliases at run time
(`--models`) because "latest" aliases drift:

| Provider | Frontier judge — alias (as of freeze) | Small-tier sibling (paired baseline) |
|---|---|---|
| OpenAI | `openai/gpt-5.6-sol` | gpt-4o-mini |
| Anthropic | `~anthropic/claude-fable-latest` | claude-haiku-4.5 |
| Google | `google/gemini-3.1-pro-preview` | gemini-2.5-flash |
| xAI | `x-ai/grok-latest` | — (no small-tier sibling tested) |

The aliases above are the intended panel; each is **validated before any real run** by
`--check-models` (one trivial call each, reporting resolve + score-parse) and the exact resolved
alias is recorded verbatim in `ccc_frontier_meta.json` with the run date. Two are moving aliases
(`*-latest`), so the metadata is authoritative for what actually ran. Within-provider capability comparisons are available for OpenAI, Anthropic, and
Google; xAI/Grok is frontier-only (no paired small-tier baseline).

## Design (Phase 1)

Per domain: **items × 4 models × 4 conditions × 2 candidate types × {score_only} × 3 reps.**
- **Conditions:** `no_injection`; `answer_only` (neutral bare wrong conclusion — **primary**);
  `full_rationale` (neutral full wrong rationale); `solver_rationale` (authoritative label).
- **Protocol:** `score_only` only (the vulnerable, low-cost protocol). `verify_written` is a
  separate, cost-gated **Phase 2** (§ Phase 2), not run unless Phase 1 shows capture.
- **Candidate types:** `correct`, `wrong_matching` (frozen; oracle-labelled).
- **Sizes:** arithmetic 1,536 cells, code 1,536, SQL 2,304 — **5,376 score_only cells total.**
- **Seed** `619273400`; rep-block deconflicted per domain.

## Primary contrast and mechanism checks

Per (domain, model), paired within item, item-clustered nonparametric bootstrap (B = 6,000),
fail-closed. **Supported** iff the 95% interval excludes zero in the predicted direction AND ≥ 75%
of the domain's items are complete.

- **PRIMARY — bare-conclusion harm (score_only):** `D(no_injection) − D(answer_only)`, predicted
  > 0. The direct CCC test for each frontier judge in each domain.
- **Mechanism increments (descriptive; not equivalence tests):** provenance increment
  `harm(solver_rationale) − harm(full_rationale)`; rationale increment `harm(full_rationale) −
  harm(answer_only)`. Intervals covering zero bound, but do not exclude, small effects.
- **Capability-gradient read (descriptive):** compare each frontier judge's bare-conclusion harm to
  its committed small-tier sibling's value in the same domain (from `FINDINGS_*`), within provider.

## Phase 2 (declared, cost-gated, not part of this freeze's run)

If Phase 1 shows capture, a separate run adds `verify_written` (same design) to test whether
frontier capability + written verification eliminates capture, via the **residual** susceptibility
under verify_written (not the mitigation delta). Phase 2 is priced and approved separately because
long verify completions dominate frontier cost.

## Integrity

- Each domain's release gate runs at start (code: item+runner hashes, sandbox self-verify; SQL:
  item hash + **gold-signature gate** on the local SQLite; arithmetic: confirmatory cache frozen).
- Streamed append-only JSONL per domain (`ccc_frontier_<domain>_obs.jsonl`) + hash-keyed prompt
  manifest; run metadata (`ccc_frontier_meta.json`) records aliases, seed, run date, worker count.
- **Concurrency invariants** (fixed pool, single writer, dedup by frozen cell identity, resume
  retries only non-successful cells, workers never raise → failures preserved) verified offline
  and reused from the SQL adapters; conservative default pool of 4 (frontier rate limits).
- Fail-closed missingness: reported before estimates, never imputed, never read as safety.
- At most one successful row per cell; deduplication key `(domain, item, model, condition,
  candidate, rep, protocol)`.

## Non-claims

- Tests **four specific frontier endpoints as of the run date**; aliases and their backing may
  change. No claim about any named benchmark or about frontier models in general.
- Frozen micro-domains (16/16/24 items); coarse 0/100 judges; directions and support calls are the
  result, magnitudes indicative.
- xAI/Grok has no paired small-tier baseline, so its capability-gradient read is absent.
- A CI covering zero is not evidence of immunity.

## Release-gate criteria

The run counts only if, at start: each domain's release gate passes (hashes / gold signature /
frozen cache); the model aliases resolved in the preflight; exactly one writer per domain-file; no
malformed or duplicate-success rows; and the missingness report precedes estimates. Given a counting
run, the headline read per domain is gated on the **primary** bare-conclusion harm: a frontier judge
is called *captured in that domain* iff its interval excludes zero and ≥ 75% of items are complete.

*Frozen. Review, validate aliases, and approve before any API run. Nothing above the run — items,
conditions, contrasts, thresholds, seed — changes after the first call without voiding the
preregistration.*
