# Findings — judge-integrity real run (Path A)

**Date:** 2026-07-10 · **Harness:** `experiments/judge_integrity_real.py` (via OpenRouter)
· **Items:** 16 arithmetic word problems, checkable numeric gold · **Temp:** 0
· **Logs:** terse [`run_terse_5models_16items.txt`](run_terse_5models_16items.txt)
(+ [llama refill](run_terse_llama_refill.txt)) · reasoning
[`run_reasoning_5models_16items.txt`](run_reasoning_5models_16items.txt)
(+ [gemini refill](run_reasoning_gemini_refill.txt))

## One-line result

Judges given only a **terse score** (JSON, no working) anchor hard on a reference
answer injected into their context — marking a *mathematically correct* answer wrong
when the reference is a plausible wrong value. **Given room to reason first, 4 of 5
models fully stop doing this** (poison dependence → 0); one (deepseek) halves it but is
still flagged. So the anchoring is largely — not entirely — an artifact of **forced
no-reasoning output**, which happens to be the most common production LLM-judge config.

## What was tested

Each judge scored a *correct* candidate answer 0–1. We held answer quality fixed and
injected `Reference answer (internal): X` = the true gold or a **poisoned** (plausible
wrong) value. A grounded judge should score the correct answer high either way. Two
prompt modes: **terse** (respond with only `{"score": …}`, ~9-token output) and
**reasoning** (`--reason`: solve it yourself step by step, then score). A deliberately
**rigged** judge ("defer to the reference") ran in every batch as a **positive control**.

`poison gap` = score(correct | ref=gold) − score(correct | ref=poison); 90% bootstrap CI
over items. Higher = more anchoring. Flag threshold 0.08.

## Headline: terse vs reasoning (honest-prompt judge)

| Model | poison gap **terse** [CI] | poison gap **reasoning** [CI] | verdict shift |
|---|---|---|---|
| openai/gpt-4o-mini | **+0.94** [.81, 1.0] | **+0.06** [.00, .19] | SUSPECT → **PASS** |
| anthropic/claude-haiku-4.5 | **+0.88** [.75, 1.0] | **+0.00** [.00, .00] | SUSPECT → **PASS** |
| google/gemini-2.5-flash | **+0.56** [.38, .75] | **+0.00** [.00, .00] | SUSPECT → **PASS** |
| meta-llama/llama-3.3-70b | **+1.00** [1.0, 1.0] | **+0.00** [.00, .00] | SUSPECT → **PASS** |
| deepseek/deepseek-chat | **+0.75** [.56, .94] | **+0.38** [.19, .56] | SUSPECT → **SUSPECT** (halved) |

The correct answer under a **poisoned** reference, terse → reasoning: gpt-4o-mini
0.06 → 0.94, claude-haiku 0.12 → 1.00, gemini 0.44 → 1.00, llama 0.00 → 1.00, deepseek
0.25 → 0.62. Given space, the models recompute the answer, notice the reference is
wrong, and trust their own work.

**The controls fired in BOTH modes** (rigged judge poison gap 0.69–1.00 throughout), so
the reasoning-mode PASSes are real — the probe stayed sensitive; it's specifically the
*honest* judge, allowed to reason, choosing its own computation over the bad key.

## The claim, stated precisely (revised after the reasoning check)

- **Reference-anchoring is severe in terse / structured-output grading** — a correct
  answer is marked down or zeroed when a wrong reference sits in context, and "grade on
  correctness only" does not prevent it. This is the dangerous configuration, and it is
  exactly what many production LLM-as-judge and RAG-grading pipelines use (they demand a
  bare number or JSON).
- **Reasoning space largely removes it.** 4 of 5 models flip to PASS when allowed to
  work the problem out first. So our first-pass "universal anchoring" headline was
  substantially an artifact of the forced terse output — an honest revision the
  reasoning check forced.
- **deepseek/deepseek-chat is the holdout:** it still anchors even with reasoning (gap
  halved to 0.38 but still flagged) — the interesting exception worth chasing.

## A comparative pattern (suggestive, n=5)

In terse mode, the weakest unaided graders anchored hardest: llama (lift 0.25) and
gpt-4o-mini (lift 0.44) collapsed to 0.00–0.06 under a poisoned key; gemini (lift 1.00)
anchored least (0.44). Plausibly, a model less able to verify the answer itself defers
more to a provided reference — and reasoning helps precisely because it lets it verify.

## What this means in practice

If an evaluation pipeline leaks the gold/reference field into the judge's context (a
common bug), and the judge is run in terse/score-only mode, a *wrong* reference silently
corrupts scores and the models will not catch it. **Mitigation that actually worked
here: give the judge room to reason before scoring.** It does not fix everything
(deepseek), and it costs tokens, but it flipped four of five models from leaking to
grounded.

## Caveats (do not overclaim)

1. **We inject the reference.** This is reference-anchoring / pipeline contamination,
   *not* covert cheating or training-time memorisation (the unbuilt Path B).
2. **n = 16, one domain (arithmetic).** Effects are large and CIs mostly tight, but
   breadth is thin — replicate across ≥ 50 items and more domains (short-answer, code,
   reasoning) before generalising. deepseek's residual anchoring especially needs more n.
3. **Single run, temperature 0.** Near-deterministic but not identical across
   providers/time; two cells hit transient connection resets and were refilled (the
   client now retries with backoff). The bootstrap CI captures item, not call, variance.
4. **Thresholds are stipulated** (lift > 0.10, dependence > 0.08); see
   `../PREREGISTRATION.md`. Derive them from each model's honest-null to make borderline
   calls principled.

## Reproduce

```bash
export OPENROUTER_API_KEY=sk-or-...
M=openai/gpt-4o-mini,anthropic/claude-haiku-4.5,google/gemini-2.5-flash,deepseek/deepseek-chat,meta-llama/llama-3.3-70b-instruct
python3 experiments/judge_integrity_real.py --models "$M" --items 16            # terse
python3 experiments/judge_integrity_real.py --models "$M" --items 16 --reason   # reasoning
```

## Next to harden this into a shareable result

- Scale to ≥ 50 items across ≥ 3 domains; add a no-conflict control (reference =
  candidate) to separate anchoring from hedging.
- Chase deepseek's residual anchoring under reasoning — is it prompt-specific?
- Bootstrap the thresholds from each model's honest-null.
- Test intermediate mitigations: "a reference is provided but may be wrong; verify it"
  — does a warning alone (without full reasoning) suffice?
