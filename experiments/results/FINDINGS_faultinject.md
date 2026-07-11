# Findings — fault injection: is the sealed solver a NEW silent authority?

**Date:** 2026-07-10 · **Probe:** `experiments/judge_faultinject.py` · **Log:**
[`run_faultinject.txt`](run_faultinject.txt) · 8 code-verified hard items · 5 models · 2 reps · temp 0

## The question, and why it needs no fallible model

The two-stage/three-stage design removes the reference from the scorer. But that only
*moves* the trusted input: the judge is now grounded in the solver's sealed solution. So:
**is the sealed solver merely a new authority the judge follows silently?** We test it
directly by INJECTING a deliberately wrong solver solution (gold is code-verified, so the
correct verdict is known for every cell) and crossing it with a correct/wrong candidate,
reference hidden.

## Result — 3 of 5 models follow the solver; 2 evaluate

| Model | false-rejection¹ | false-acceptance² | discrimination under a wrong solver³ | verdict |
|---|---|---|---|---|
| openai/gpt-4o-mini | **+0.50** | **+0.38** | **−0.25** | follows the solver |
| deepseek/deepseek-chat | **+0.44** | **+0.56** | **−0.25** | follows the solver |
| meta-llama/llama-3.3-70b | **+0.38** | **+0.56** | **−0.25** | follows the solver |
| anthropic/claude-haiku-4.5 | −0.12 | +0.08 | +0.25 | still evaluates |
| google/gemini-2.5-flash | −0.19 | +0.12 | +0.31 | still evaluates |

¹ how much a *correct* candidate is downscored when the injected solver is wrong (higher =
worse). ² how much a *wrong* candidate is upscored when a wrong solver matches it. ³
score(correct candidate) − score(wrong-but-matching candidate), **both under a wrong
solver**: **negative means the judge scores the wrong-but-matching answer *higher* than the
correct one** — it is grading "does the candidate match the solver," not "is it correct."

For gpt-4o-mini, deepseek and llama the sealed solver **silently controls the verdict**: a
wrong solver makes them reject correct work (+0.38 to +0.50) and accept matching wrong work
(+0.38 to +0.56), and their discrimination goes *negative*. claude-haiku and gemini resist —
they score the correct candidate high (1.00, 0.88) even when the solver is wrong, and keep
positive discrimination. A real, load-bearing model split.

## But no single source is safe: exposing a reference still anchors everyone

| Model | reference RESCUE of a wrong solver | reference POISONING of a correct case |
|---|---|---|
| openai/gpt-4o-mini | +0.50 | +0.62 |
| deepseek/deepseek-chat | +0.62 | +0.44 |
| meta-llama/llama-3.3-70b | +0.62 | +0.38 |
| anthropic/claude-haiku-4.5 | +0.00 | +0.25 |
| google/gemini-2.5-flash | +0.12 | +0.38 |

The solver-followers also follow the reference when it is present (rescue +0.50 to +0.62 —
they swing to whichever authority is on file). And **every** model, including the two that
resist the solver, is damaged by a poisoned reference when it is exposed (+0.25 to +0.62).
So the clean-pipeline rule (keep the reference out of the judge) remains necessary — but it
is not sufficient, because the solver is now a second privileged channel.

## Conclusion (the uncomfortable, valuable one)

**Removing the reference from the judge blocks reference leakage, but grounding the judge in
a sealed solver output creates another authority channel that most models here follow
silently.** Safety is not achieved by swapping one privileged answer source for another. It
requires:

- **conflict routing** — surface solver/candidate/reference disagreement rather than letting
  any one of them silently decide; and
- **independent verification** — a deterministic checker, a second genuinely independent
  solver, or human adjudication — because when two sources disagree, the auditor can only
  honestly conclude **"conflict detected; attribution unresolved."** Disagreement does not
  identify which side is wrong (the two could even share a systematic error).

The three-stage architecture's *valid* safety property is therefore narrow and real: **it
converts silent influence into an explicit, unresolved conflict.** It does not, by itself,
tell you who is right.

## Caveats

- n = 16 trials/model/cell (8 items × 2 reps); scores are coarse and CIs would be wide.
  Treat the **directions and the model split** as the finding, not the exact magnitudes.
- The injected solver/candidate solutions were model-generated (cached in
  `faultinject_solutions.json` for reproducibility); their persuasiveness varies by item.
- Single run, temp 0 (not deterministic across a hosted API). Numeric domain only.

## Supplementary: the hard-item three-stage run

`run_threestage_hard.txt` (abstain now counted separately from wrong): on hard numeric items
the models' "fallibility" is mostly **abstention, not wrong answers** (abstain 12–88%; clean
wrong ≈ 0, gpt-4o-mini 1) — a comparatively *safe* failure mode, since an abstaining solver
routes to review. The candidate→solver pull was small but **non-zero for gpt-4o-mini (22%)
and llama (17%)** and 0% for the others — i.e. the candidate→solver channel is not closed for
every model, consistent with the fault-injection split. Review-load was abstention-dominated.
