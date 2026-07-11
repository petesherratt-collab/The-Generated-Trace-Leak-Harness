# Findings — three-stage prototype (solver blind to candidate + reference)

**Date:** 2026-07-10 · **Probe:** `experiments/judge_threestage.py` · **Log:**
[`run_threestage.txt`](run_threestage.txt) · 10 harder multi-step items · 5 models · 3 reps · temp 0

> **Honest headline: this run UNDER-DELIVERED on its core aim.** The two channels it was
> built to stress — candidate→solver contamination and review-load — barely fired, because
> the "harder" items were not hard enough for these five models (blind solver accuracy ≈
> 100%). The negative results below are therefore **underpowered nulls, not reassurance.**

## Summary

| Model | solver acc (blind) | candidate→solver pull | judge: correct / persuasive-wrong | ref anchoring (judge exposed) | review-load = 1−acc |
|---|---|---|---|---|---|
| gpt-4o-mini | 100% | 0% | 1.00 / 0.10 | +0.08 | 0% [0,11] |
| claude-haiku-4.5 | 100% | 0% | 1.00 / 0.01 | +0.00 | 0% [0,11] |
| gemini-2.5-flash | 100% | 0% | 1.00 / 0.00 | **+0.20** | 0% [0,11] |
| deepseek-chat | 100% | 0% | 1.00 / 0.03 | +0.00 | 0% [0,11] |
| llama-3.3-70b | 97% | 0% | 1.00 / 0.15 | +0.07 | 3% [1,17] |

(n = 30 trials/model. CIs are Wilson 95%.)

## What this run does NOT show

- **Candidate→solver contamination: not tested, not absent.** Pull = 0% everywhere — but
  the solver got the answer right on ~100% of trials, so the persuasive-wrong candidate had
  nothing to exploit. A contamination channel can only be measured where the solver is
  uncertain or wrong; that state essentially never occurred. **0% pull here is an
  underpowered null, not evidence the channel is safe.** (llama's cand_effect of −3% is
  noise: on its one blind error, seeing even a wrong candidate happened to nudge it right.)
- **Review-load dynamics: barely exercised.** review-load = 1 − solver accuracy was 0% for
  four models and 3% for llama (its single solver error, correctly routed). The *mechanism*
  the review predicted is confirmed in miniature — routing load tracks solver error — but at
  ~0 magnitude, so nothing is stressed. To see it, solver accuracy must drop well below 100%.
- **The "harder" item set was not hard for frontier-class endpoints.** Item difficulty (or
  model strength) is the lever that was mis-set; that is the honest limitation of this run.

## What it does show (real, but modest)

- **The three-stage judge discriminates well when grounded in a correct solver solution.**
  Correct candidate ≈ 1.00, persuasive-wrong candidate 0.00–0.15 (discrimination +0.85 to
  +1.00), with **no reference in context**. So a judge anchored to an independent, correct
  solution rejects a persuasive wrong answer. Caveat: this leaned entirely on the solver
  being right; if the solver errs, the judge is grounded in a wrong solution — untested here.
- **Exposing the judge to the reference still anchors it.** Even in this stronger setup and
  with a correct independent solution present, gemini's judge moved **+0.20** toward the
  reference (others 0.00–0.08). This re-confirms why the clean pipeline withholds the
  reference from the scorer: leaking it still bites, most for gemini.
- The auditor's known-poison disagreement sensitivity was 100% — but that is downstream of
  100% solver accuracy (the solver disagreed with every poisoned key because it was right),
  so it inherits the same underpowering.

## Correct next step: actually drop solver accuracy

The design is right; the difficulty was mis-calibrated. To measure the candidate→solver
channel and the review-load curve, push blind solver accuracy into ~50–80% by either:

- **weaker/smaller models** (e.g. an 8B-class endpoint) on these same items, and/or
- **genuinely hard items** (competition-style, multi-constraint, or ambiguous problems).

Then re-measure: does a persuasive-wrong candidate raise the solver's decoy rate; does
review-load rise as 1 − accuracy; and — the untested worry — when the solver is wrong, does
the judge (grounded in that wrong solution) mis-score, and does the auditor's disagreement
then reflect a bad *solver* rather than a bad *reference*? That attribution question is the
real one, and it only becomes visible once the solver is fallible.

## Caveats

- n = 30 trials/model; single run; temp 0 (not deterministic across a hosted API).
- Numeric-answer domain with mechanical comparison; open-ended tasks remain untested and are
  where the Stage-2/auditor comparison becomes a judge of its own.
