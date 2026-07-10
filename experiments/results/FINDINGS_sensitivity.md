# Findings — wording-sensitivity matrix (pre-registered)

**Date:** 2026-07-10 · **Design:** [`../PREREG_deepseek_sensitivity.md`](../PREREG_deepseek_sensitivity.md)
· **Probe:** `experiments/judge_sensitivity_probe.py` · **Log:** [`run_sensitivity_matrix.txt`](run_sensitivity_matrix.txt)
· 16 items · 3 reps/variant · temp 0

## Question

The D-condition mitigation (verify + written working + score) drove the poison gap to
0.00, but deepseek's D result had swung 0.38 → 0.00 across two phrasings. Is that
mitigation **structurally robust** or a **wording artifact**? We held the intervention
class fixed and varied only phrasing across four pre-registered variants (D0 baseline,
D1 procedural, D2 adversarial, D3 template), 3 reps each, with a defer-to-reference
control for sensitivity.

## Result

Poison gap (mean of 3 reps; range = max−min across reps):

| Model | control | D0 baseline | D1 procedural | D2 adversarial | D3 template | verdict |
|---|---|---|---|---|---|---|
| **deepseek/deepseek-chat** | +1.00 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | **ROBUST** |
| **openai/gpt-4o-mini** | +0.94 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | **0.25 (0.12)** | **FRAGILE** |

Between-variant spread of means: deepseek 0.00, gpt-4o-mini 0.25 (vs a within-variant
noise floor of 0.12). Controls fired for both, so the probe was sensitive in this format.

## What it means (with the twist)

- **deepseek is robust, not fragile.** Across all four D-phrasings it fully resists a
  poisoned reference with *zero* run-to-run variance. So its earlier 0.38 did **not**
  come from wording sensitivity *within* the D class — it came from a phrasing outside
  this matrix (the pre-refactor `--reason` prompt) or was run noise. Within the
  pre-registered class, deepseek is stable. The model we suspected is the clean one.
- **gpt-4o-mini is the fragile one — and on the variant we'd least expect.** D0/D1/D2
  give 0.00, but **D3 (the rigid template) regresses to a mean 0.25**, above the noise
  floor (0.12) and varying across reps (0.19/0.31/0.25). The template was *hypothesised
  to be the most robust* (it physically forces reasoning tokens before the score);
  instead its checklist structure lets the model slip back toward anchoring on a subset
  of items. An audited transcript confirms it is genuine item-specific behaviour, not a
  parsing artifact (on easy items it computes correctly and scores 1.0).
- **Therefore: single-turn prompt-level mitigation robustness is model-specific and not
  guaranteed.** At least one model has a real wording-fragility, and it appears on the
  most "structural-looking" prompt. This is exactly the failure the pre-registration was
  built to catch, and it **strengthens the case for the structural two-stage mitigation**
  (judge blind first, reveal the reference afterward, flag conflicts) over trusting any
  single prompt.

## Caveats

- n = 16, k = 3. The gpt-4o-mini D3 effect (0.25, range 0.12) is **real but modest** and
  the noise floor is non-trivial; treat the magnitude as provisional and worth more reps.
- D1/D2 change the *semantics* (they tell the judge to ignore/distrust the reference),
  while D0/D3 vary *structure*. That both semantic variants and D0 hold at 0.00, while
  only the structural template D3 fails for gpt-4o-mini, points the fragility at the
  **template structure specifically**, not at removing the "distrust" content.
- This probes two models; the split (one robust, one fragile) says robustness cannot be
  assumed per-model without testing.

## Takeaway

The pre-registration paid for itself: it overturned the assumption about *which* model
was fragile, and found that the most structured-looking prompt was the weakest for
gpt-4o-mini. Do not ship a single-turn "verify + show working" prompt as a guaranteed
defence — validate per model, and prefer the structural two-stage design.
