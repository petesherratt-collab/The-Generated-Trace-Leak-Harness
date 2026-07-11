# Findings — provenance cross: authority deference vs persuasion

**Date:** 2026-07-10 · **Probe:** `experiments/judge_provenance.py` · **Log:**
[`run_provenance.txt`](run_provenance.txt) · 8 code-verified items · 5 models · 2 reps · temp 0

## Question

The fault-injection result showed judges follow a wrong sealed solver. Two mechanisms,
different fixes: (1) **authority deference** — the "sealed solver" *label* confers privileged
truth; (2) **persuasion** — the wrong analysis simply reads convincingly, whatever it is
called. We present the *same* wrong analysis text under different provenance framings while
scoring a **correct** candidate (reference hidden), and measure the drop in the correct
candidate's score (influence = baseline − score).

## Result — both mechanisms, model-dependent (and neither prompt fix suffices)

Influence = how far the correct candidate's score is dragged DOWN (higher = worse):

| Model | base | solver-label | untrusted-label | may-contain-errors | no label | bare answer | reasoning only | authority effect¹ |
|---|---|---|---|---|---|---|---|---|
| openai/gpt-4o-mini | 0.69 | +0.41 | +0.44 | +0.34 | +0.47 | +0.56 | +0.22 | **+0.02** |
| anthropic/claude-haiku-4.5 | 1.00 | +0.12 | +0.00 | +0.00 | +0.12 | +0.12 | +0.00 | **+0.12** |
| google/gemini-2.5-flash | 0.81 | +0.12 | −0.06 | +0.12 | +0.19 | +0.06 | +0.12 | +0.09 |
| deepseek/deepseek-chat | 0.84 | +0.44 | +0.19 | +0.22 | +0.41 | +0.34 | +0.34 | **+0.23** |
| meta-llama/llama-3.3-70b | 0.88 | +0.56 | +0.31 | +0.50 | +0.81 | +0.06 | +0.38 | +0.16 |

¹ authority effect = influence(solver-label) − mean(influence of untrusted/may-contain-errors).
Positive ⇒ the "solver" label specifically adds power.

**Per model:**
- **gpt-4o-mini — pure persuasion, no authority effect (+0.02).** The wrong text drops the
  correct candidate ~0.4 *regardless of label* — even labelled "UNTRUSTED, may be adversarial"
  it is still followed (+0.44, if anything ≥ the solver label). And a bare wrong answer
  (+0.56) moves it more than the reasoning (+0.22): it is averse to a conflicting *answer*,
  not deferring to a *source*.
- **claude-haiku — clean authority discrimination (+0.12), small magnitude.** It correctly
  *ignores* material framed "untrusted/may-contain-errors" (influence 0.00) but is moved by the
  "solver" label and by a bare answer. It grants a trust channel by provenance — the good news
  is it discounts untrusted material; the caveat is the "solver" label is a channel.
- **deepseek — both (+0.23 authority premium) and persuasion.** The solver label roughly
  doubles the influence vs untrusted (0.44 vs 0.19), but untrusted still drops it (persuasion
  present); answer and reasoning matter equally.
- **llama — both (+0.16), reasoning-driven.** A "solver" premium, but the *reasoning* does the
  work (reason +0.38 vs bare answer +0.06), and a naked unlabelled analysis is most influential
  of all (+0.81).
- **gemini — weak/mixed**, effects near the noise floor at this n.

## The load-bearing implication

**Prompt-level de-authorization does not fix it.** For most models, framing the wrong analysis
as *untrusted / possibly adversarial / unlabelled* did **not** neutralize its influence — the
judge still downscored correct work when confronted with a plausible conflicting analysis
(gpt-4o-mini most starkly). So you cannot mitigate this by simply not calling a source
"authoritative." A real "solver" authority premium *also* exists for several models (claude,
deepseek, llama), so removing the label helps some models but not others.

Because **neither** relabeling nor de-privileging is sufficient across models, the mitigation
must be structural: **conflict routing + independent verification.** This is a stronger reason
for the routed architecture than the fault-injection result alone — it rules out the cheap
prompt fix ("tell the judge the solver might be wrong").

## Caveats

- n = 16/cell (8 items × 2 reps); small effects (claude, gemini) are within noise. The
  **per-model mechanism pattern is the finding**, not the exact magnitudes.
- Baselines vary (0.69–1.00): on some hard items the judge is already unsure of the correct
  candidate, which widens the measurement. Single run, temp 0, numeric domain.
- Not yet separated (a remaining confound, lower priority now that persuasion is shown to
  dominate for gpt-4o-mini): whether the fault-injection *false-acceptance* was partly lexical
  agreement between the wrong solver and the matching wrong candidate — the "answer-agreement
  vs narrative-agreement" matrix.

## Where this leaves the architecture

The routed design stands and is now better justified: judge each source separately, compare
mechanically, route disagreement to a deterministic verifier / second independent solver /
human, keep originals immutable. The provenance result shows why a prompt-only fix is not
enough — the judge is swayed by a conflicting analysis's *content*, not merely its claimed
authority.
