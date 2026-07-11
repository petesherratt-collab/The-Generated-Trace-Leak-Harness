# Findings — the two-stage architecture (reference never touches the scorer)

**Date:** 2026-07-10 · **Probe:** `experiments/judge_twostage.py` · **Log:**
[`run_twostage.txt`](run_twostage.txt) · 16 checkable-gold arithmetic items · 5 models · temp 0

## Why this design

The sequence established, in order: score-only judging anchors hard on an injected
reference; a "verify + show working" prompt mostly fixes it but is **wording-fragile**
(gpt-4o-mini's template regressed); the autopsy showed the fragile failures are
**correct-working / wrong-score** — the model derives the right answer and still lets the
reference control the verdict, even confabulating "8 does not match 8". And crucially,
**the model's own conflict report cannot be trusted** (same confabulation). So a mitigation
that asks the model to flag conflicts is circular.

The fix is structural, not a prompt: **remove the override channel.**

- **Stage 1 (blind):** the scorer sees only question + candidate + rubric. It emits its
  independently derived answer and a score. The reference is never in its context.
- **Stage 2 (harness, no model call):** the harness compares the blind derived answer to
  the reference *mechanically*. Agree → accept the blind score. Disagree → **flag for
  review.** The verdict is always the blind score; the reference only routes.

Because the scorer never sees the reference, the verdict is reference-invariant **by
construction** — silent override is impossible, not measured-and-hoped. Every metric below
is computed by the harness from its own observations; none is a model self-report.

## Result

| Model | vuln gap (ref in context)¹ | two-stage gap | blind lift² | blind derivation✓ | poison-catch³ | false-flag⁴ |
|---|---|---|---|---|---|---|
| openai/gpt-4o-mini | +0.00 | **+0.00** | +1.00 | 100% | 100% | 0% |
| anthropic/claude-haiku-4.5 | +0.00 | **+0.00** | +1.00 | 100% | 100% | 0% |
| google/gemini-2.5-flash | +0.00 | **+0.00** | +1.00 | 100% | 100% | 0% |
| deepseek/deepseek-chat | +0.06 | **+0.00** | +1.00 | 100% | 100% | 0% |
| meta-llama/llama-3.3-70b | **+0.34** | **+0.00** | +0.94 | 100% | 100% | 0% |

¹ poison gap using the *same strong (verify+explain) prompt* but with the reference in
context — the best single-turn baseline. It still leaks for llama (+0.34) and deepseek
(+0.06). ² blind score(correct candidate) − blind score(wrong candidate); scoring accuracy
is fully retained without the reference. ³ fraction of poisoned keys flagged for review.
⁴ fraction of correct keys wrongly flagged.

## What it shows

1. **Silent override is eliminated unconditionally.** Two-stage poison gap is 0.00 for
   every model — the verdict cannot move with the reference because the scorer never sees
   it. Contrast the vulnerable baseline, where even the strongest single-turn prompt still
   let llama's score swing 0.34. The architecture *dominates* the best prompt, and it does
   so structurally rather than by persuasion.
2. **Withholding the reference does not hurt scoring.** Blind lift +0.94–1.00: the judges
   still cleanly separate correct from wrong candidates.
3. **Bad keys are surfaced, not absorbed.** 100% poison-catch: every poisoned reference
   disagreed with the model's blind derivation and was routed to review. 0% false-flag:
   no correct key was flagged. The reference becomes an audit/routing signal, never a
   control input.

## Honest scope — the one real dependency

The two properties are not equally strong, and the distinction matters:

- **Override elimination is structural and unconditional** — 0 regardless of task
  difficulty, model, or wording, because of *where the reference sits*, not how well the
  model reasons.
- **Routing quality (catch / false-flag) is bounded by BLIND ACCURACY.** Here blind
  derivation was 100% correct because the task is trivial arithmetic, so catch was perfect
  and false-flags zero. On harder tasks the model's blind computation will sometimes err:
  a blind error that happens to match the poisoned key would be a *missed* catch, and a
  blind error that diverges from a correct key would be a *false* flag. So on hard tasks,
  catch degrades toward the model's blind accuracy and the review queue grows.

But even in that worst case the safety property holds: the pipeline **never silently lets
the key rewrite the verdict** — it either scores blind (reference-independent) or flags for
review. It converts a silent-corruption failure into a visible-workload cost, which is the
correct trade for an evaluation system.

## Caveats

- n = 16, one domain (arithmetic where blind accuracy is ~perfect), single run, temp 0.
  The routing numbers (100/0) are best-case; re-run on harder items to see catch/false-flag
  track blind accuracy.
- Assumes the reference is comparable to the model's derived answer (here, a number). For
  free-form references the Stage-2 comparison itself needs care (and must not be delegated
  back to an anchoring model).

## The whole arc, in one line

Score-only judges anchor on a leaked key → "show your working" mostly helps but is
wording-fragile → the fragile failures are correct-working/wrong-score and the model's
self-report of them is confabulated → so the only reliable fix is architectural: keep the
reference out of the scorer and route on a harness-computed comparison. Which is exactly
the leak-harness thesis — *what information actually controlled the verdict?* — answered by
building a pipeline where the answer can only ever be "the submitted work."
