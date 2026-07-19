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
| xAI | `x-ai/grok-4.5` | — (no small-tier sibling tested) |

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

---

## Amendment 1 — output-token budget (2026-07-19): instrument defect, corrected re-run

**What was wrong.** The first Phase-1 run (2026-07-19) used a `score_only` completion budget of
60 tokens (240 on retry), tuned for the terse small-tier judges. Frontier judges are **reasoning
models**: their reasoning tokens count against the completion budget, so they were **truncated
before emitting the verdict**. A compounding code defect made it worse — `parse_score` returns
`None` (it does not raise), so the intended larger-budget retry, which lived in an `except` branch,
**never fired**; every truncated cell failed on the first 60-token call with no retry.

**Effect on the first run (why it is not the frontier result).** Missingness was
**model-specific**, not random — the signature of an instrument limit, not of behaviour:
`gemini-3.1-pro-preview` ~60–67% missing (n=0 measurable in every domain),
`claude-fable-latest` 25–46% (all below the completeness floor), vs `gpt-5.6-sol` 2–10% and
`grok-4.5` 0–3%. Two of four judges produced essentially no data. Their absence of a measurable
harm estimate is **truncation, not immunity**, and must not be read as "no capture."

**What changed (this file's run parameters only; items/conditions/contrasts/thresholds/seed
unchanged).**
- `MAX_TOK["score_only"] 60 → 1024`, `RETRY_TOK["score_only"] 240 → 2048` (verify_written likewise
  raised for the later Phase 2). Terse judges stop early and are billed on actual tokens, so the
  headroom is free for them and necessary for the reasoners.
- `judge_once` now treats a `None` parse as failure and actually performs the larger-budget retry;
  it records the provider `finish_reason` per cell so the missingness table distinguishes
  `truncated_no_score` from `unparseable_no_score`.
- The preflight now counts a model **only if its score parses** (previously "resolved" meant merely
  "did not error"), and `--run` self-runs that preflight and **aborts** on any unvalidated model
  (override `--force-models`), so a judge that cannot emit a parseable score can never silently
  fail-closed into a false "no capture."

**Status of prior data.** The 2026-07-19 run is **retained as evidence of the defect and void for
the frontier claim.** The corrected run re-runs **all four models uniformly** under the new budget
so the panel is comparable; cherry-picking the two judges that happened to survive is not done. The
only cells from the first run that were interpretable at the floor — `grok-4.5` and `gpt-5.6-sol`
captured in SQL (~+35), `grok-4.5` no-capture in code — are treated as a **preview to be
reconfirmed**, not as findings, until the uniform corrected run reproduces them.

**Added validity check for the corrected run.** Completeness must be **condition-balanced**: if
reasoning length tracks the injected conflict, residual truncation could bias the contrast rather
than only shrink n. The corrected run reports missingness per (model × condition), and any judge
whose remaining truncation concentrates in the injection conditions is reported as unmeasurable for
that contrast rather than estimated.
