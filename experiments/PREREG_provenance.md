# Pre-registration — provenance-injection real-model run

Frozen before the real run. Harness: `provenance_injection_harness.py` (rev3, all review
fixes in). Adapter: `run_provenance_injection.py`. Direction convention: every "harm" =
disc(baseline) − disc(condition); **positive = more capture / worse discrimination**.

## Primary contrasts (confirmatory; everything else is exploratory)

Declared in advance so we do not fish. An effect is **supported** iff its 95% item-clustered
bootstrap CI excludes 0 in the predicted direction, computed **fail-closed** (require_reps:
an item is dropped unless every required cell is complete), after the missingness report.

1. **injection harm** — `disc(no_injection) − disc(neutral, full_wrong_rationale)`, per
   protocol. *Predicted > 0*: a wrong analysis captures the judge even with a neutral label.
2. **provenance harm** — `disc(neutral) − disc(solver)`, full rationale, per protocol.
   *Predicted ≥ 0*: naming the source "Solver" adds capture over a neutral label.
3. **rationale harm** — `disc(answer_only) − disc(full_wrong_rationale)` at the neutral label,
   per protocol. *Predicted > 0*: a full wrong rationale captures more than a bare wrong answer.
4. **protocol mitigation** (the headline architectural test) — diff-in-diff
   `harm(score_only) − harm(verify_written)` on contrasts 1 and 2. *Predicted > 0*: written
   independent verification reduces capture. If it does **not** (CI includes 0), the capture is
   architectural, not merely a score-only artefact.

## Secondary / exploratory (report, but no strong claims)
Header/presentation effect (neutral vs unlabelled); reviewer/candidate identity; sealed-vs-
ordinary solver status; reliability claims (verified / unverified / possibly-erroneous vs
no-claim); the five control contrasts. Multiple-comparison caveat applies — these are
hypothesis-generating.

## Design (fixed)
- **Items:** the 8 code-verified hard items (gold computed in code); frozen `items_sha256`
  recorded in run metadata. Confirmatory stage wants ≥ 16.
- **Models:** openai/gpt-4o-mini, anthropic/claude-haiku-4.5, google/gemini-2.5-flash,
  deepseek/deepseek-chat, meta-llama/llama-3.3-70b-instruct.
- **Protocols:** score_only and verify_written (both, for the interaction).
- **Candidate types:** correct, wrong_matching (primary); the two control candidates added
  only in the controls stage.
- **Repetitions:** ≥ 2 (deconflicted, non-adjacent). Confirmatory: ≥ 3.
- **Injected/candidate texts:** model-generated once, cached and frozen (`provinj_texts.json`);
  the injected wrong "solver" and matching wrong candidate are generated separately (Phase-1
  leakage audit reports their overlap, to keep conclusion-agreement distinct from wording).

## Staging (to bound cost and multiple comparisons)
1. **Primary:** identity × content (`factorial_conditions`) × 2 protocols × {correct, wrong} —
   estimates contrasts 1–4 across all 5 models.
2. **Status + reliability:** add `solver_status_conditions` + `reliability_conditions`.
3. **Controls:** add `control_conditions` and the two control candidate types — only for models
   that showed capture in stage 1.
4. **Confirmatory:** re-run the supported primary contrasts with a fresh schedule seed and ≥ 16
   items / ≥ 3 reps.

## Policies
- **Missingness:** print `missingness_report` before any estimate; if a factor (model/protocol/
  condition/candidate) shows a materially higher failure rate, treat complete-case contrasts on
  it as unreliable. Primary contrasts are fail-closed.
- **Evidence:** stream observations + prompt manifest to JSONL; record run metadata (commit,
  items hash, config) at start. Every reported number is auditable back to a transcript.
- **Stop rule:** fix stage sizes here; run once per stage; do not add conditions or nudge
  thresholds after seeing the target's numbers.
