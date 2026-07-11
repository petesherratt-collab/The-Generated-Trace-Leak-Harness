# Findings — two-stage prototype (reference withheld from the scorer)

**Date:** 2026-07-10 · **Probe:** `experiments/judge_twostage.py` · **Log:**
[`run_twostage.txt`](run_twostage.txt) · 16 checkable-gold arithmetic items · 5 models · temp 0

> **Status: proof of concept, not a capstone.** This exposes the next experiment. A prior
> version of this file over-claimed; corrections below (see "What these numbers do and do
> NOT establish"). The architectural principle is sound; the empirical conclusions are narrow.

## The principle (this part is genuinely strong)

**Information that must not influence a decision should not enter the decision-making
component's context.** That is stronger than any instruction ("reason independently",
"verify carefully", "don't anchor") — the sensitivity matrix showed instructions are
wording-fragile, and the autopsy showed the model's own conflict report is not trustworthy.
So: withhold the reference from the scorer, and route on a comparison the *harness* computes.

- **Stage 1 (blind to the reference):** scorer sees question + candidate + rubric, emits an
  independently derived answer and a score. The reference is not in its context.
- **Stage 2 (harness, no model call):** compare the derived answer to the reference
  mechanically. Agree → accept the blind score. Disagree → route to review. The verdict is
  the blind score; the reference only routes.

## What these numbers do and do NOT establish

- **"Two-stage gap = 0.00" is structural, not empirical.** If the verdict is assigned from
  the blind call and never recomputed after the reference is introduced, a reference-induced
  gap *must* be zero. Running it across five models verifies the *implementation* did what
  the code says — it is testing that a disconnected wire carries no signal. It is **not**
  evidence that any model or prompt is more robust. Do not read the 0.00 column as a result.
- **The blind scorer is reference-blind but NOT candidate-blind.** It still sees the
  candidate and is asked to "independently derive" the answer — so the candidate can steer
  that derivation. This closes the reference→score channel and leaves the candidate→solver
  channel open. On trivial arithmetic that may not bite; on ambiguous/adversarial inputs it
  can. This is the main limitation, not a footnote (see next experiment).

## Result (read as a prototype demonstration, with corrected metric names)

| Model | vuln gap¹ (ref in context) | blind lift² | blind derivation ✓ | known-poison disagreement sensitivity³ | review-routing rate on correct refs⁴ |
|---|---|---|---|---|---|
| openai/gpt-4o-mini | +0.00 | +1.00 | 100% | 100% | 0% |
| anthropic/claude-haiku-4.5 | +0.00 | +1.00 | 100% | 100% | 0% |
| google/gemini-2.5-flash | +0.00 | +1.00 | 100% | 100% | 0% |
| deepseek/deepseek-chat | +0.06 | +1.00 | 100% | 100% | 0% |
| meta-llama/llama-3.3-70b | **+0.34** | +0.94 | 100% | 100% | 0% |

¹ poison gap using the *same strong (verify+explain) prompt* but with the reference in
context — the best single-turn baseline. Still leaks for llama (+0.34) and deepseek (+0.06):
**this is the real empirical content** — reference influence persists even under a verify
prompt. ² blind score(correct candidate) − blind score(wrong candidate). ³ fraction of
poisoned refs that DISAGREED with the blind derivation (renamed: the harness detects
*disagreement*, not that the reference is the wrong side — the experimenter supplies the
poison label). ⁴ fraction of correct refs that triggered review.

The routing metrics are **best-case**: 100/0 only because blind derivation was 100% correct
on trivial arithmetic. The harness cannot say "bad key caught"; it can only say "independent
solution and supplied reference disagree." Which side is wrong is decided by the label we
already hold, not by the system.

## Claims supported by this work

- A model can produce correct visible working while issuing a verdict inconsistent with it
  (autopsy).
- Supplying a reference can influence a model judge even when the prompt requests independent
  verification (vuln gap +0.34 for llama here; the sensitivity matrix for gpt-4o-mini).
- Model-generated explanations and conflict declarations are not reliable measurements of
  reference influence (the "8 ≠ 8" transcript).
- Preventing the scoring component from receiving the reference structurally removes the
  direct reference→score pathway (by construction).

## Claims NOT yet supported (previously overstated here)

- That the architecture "dominates the strongest prompt" *generally* — shown only on trivial
  arithmetic.
- That bad keys are reliably *identified* — the system detects disagreement, not fault.
- That withholding the reference has no accuracy cost beyond arithmetic — untested on hard/
  open-ended tasks.
- That "the only thing controlling the verdict is the submitted work" — the verdict is also
  shaped by the question, rubric, candidate presentation, model, decoding, and the candidate
  can still contaminate the "independent" derivation.

## Caveats

- n = 16, one domain (exact arithmetic: canonical answer, deterministic comparison, no
  partial credit, no semantic-equivalence problem). Most real judging tasks (essays, code,
  forecasts) lack these, and there the Stage-2 comparison becomes a judge of its own.
- Temperature 0 does **not** guarantee reproducibility across hosted APIs (provider routing,
  model revisions, batching). Read the intermittent failures as "variation occurred despite
  temp 0," not "temp 0 is otherwise deterministic."

## The next decisive experiment: separate the solver from BOTH channels

Three-stage design, manipulating candidate and reference **independently** while holding the
problem fixed:

- **Solver** — question + rubric only. Sees neither candidate nor reference. Produces a sealed solution.
- **Judge** — candidate + rubric + the solver's sealed solution. Never sees the reference.
- **Auditor/router** — compares the sealed solution to the reference outside the judge; disagreement routes to review, cannot change the score.

Four conditions (solver sees candidate? × judge sees reference?): clean / candidate-contaminated
/ reference-contaminated / fully-exposed. Report: blind-solver accuracy; judge accuracy vs
human-verified labels; reference causal effect on scores; **candidate causal effect on the
solver's output**; review-routing rate; attribution of routed cases (bad ref vs bad solver vs
ambiguity); and per-trial failure rates with uncertainty intervals — on genuinely hard and a
few open-ended tasks, not just arithmetic.

Until the solver is separated from the candidate too, this prototype is **reference-blind but
not genuinely independent.**
