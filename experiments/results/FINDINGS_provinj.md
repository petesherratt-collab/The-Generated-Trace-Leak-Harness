# Findings — provenance × content factorial (corrected harness)

**Date:** 2026-07-10 · **Harness:** `experiments/provenance_injection_harness.py` (review-corrected)
· **Adapter:** `run_provenance_injection.py` · **Log:** [`run_provinj.txt`](run_provinj.txt)
· 8 code-verified items · 5 models · reps=1 · temp 0 · scores 0–100

> **Read this as directional, not precise.** reps=1 and n=8 items make the item-clustered
> bootstrap CIs wide; most *per-label* contrasts straddle zero. Only the large, cross-model
> effects below are trustworthy. This corrects and refines the earlier provenance probe; it
> does not overturn it.

## Confound cleared first (Phase 1)

The injected wrong "solver" analysis and the matching wrong candidate share only **word-4gram
Jaccard 0.083** (question content excluded) while agreeing on the conclusion 8/8. So the
false-acceptance seen earlier rides on **conclusion agreement, not shared wording** — the
agreement-leakage confound the review flagged is not driving the effect.

## Robust signals (cross-model, CIs mostly excluding zero)

1. **Injecting a wrong analysis — even UNLABELLED — collapses discrimination.**
   `injection[unlabelled full − no_injection]` (discrimination = score(correct) − score(wrong)):
   gpt-4o-mini −75 [−111,−40], llama −87 [−137,−25], claude −54 [−104,−10], gemini −39 [−80,0],
   deepseek −15 [−55,20]. Robust for 3–4 of 5. **A plausible wrong analysis with no authority
   badge at all is enough to make judges stop telling correct from wrong candidates.** Content,
   not provenance, is the primary driver — consistent with the earlier "persuasion dominates."

2. **A skepticism label partially RESTORES discrimination — against a bare wrong answer.**
   `authority[low_authority("Untrusted") − unlabelled] | wrong_answer_only`: gpt +32 [7,59],
   gemini +64 [24,101], deepseek +71 [38,105], llama +50 [13,88], claude +70 [−0.4,136]. Robust
   4/5. Labelling a bare wrong answer "Untrusted Candidate Analysis" makes judges correctly
   discount it — **provenance does matter for a bare claim.**

3. **…but a persuasive wrong RATIONALE largely defeats the skepticism label.** Under
   `full_wrong_rationale`, the "Untrusted" restoration weakens or reverses (gpt −20, claude −16;
   `rationale[full − answer_only] | low_authority` is strongly negative, gpt −42 [−74,−11]). A
   convincing wrong argument overrides "this may be untrusted" in a way a bare wrong answer does
   not.

4. **Explicit reliability claims move judges in the sensible direction.** "May contain errors"
   restores discrimination (gpt +14 [5,25], claude +19 [2,44], llama +50 [13,88]); a **"verified"
   claim reduces it** (deepseek −29 [−56,−4], gemini −31 [−63,0]) — a false "verified" badge makes
   judges defer to a wrong analysis. Reliability framing is a real, if secondary, lever.

## Weak / at-noise-floor

A specific **"Sealed Solver" authority premium** over the unlabelled baseline is mostly small
and inconsistent (clear only for deepseek, −29 under full rationale). Likely a **ceiling
effect**: the unlabelled wrong content already collapses discrimination, leaving little room
for the label to add. Most fine-grained authority-gradient contrasts straddle zero at this n.

## Answer to the two-mechanism question

**Both mechanisms are real, but persuasion (content) dominates and provenance/reliability is a
secondary modulator.** A wrong analysis sways judges even with no label; skepticism labels help
against a bare claim but are **overpowered by a convincing wrong rationale**; a "verified" claim
worsens deference. So the failure is not primarily "the *solver* badge is magic" — it is
"a plausible wrong argument is persuasive, and labels only partly counter it."

## Why this hardens the architectural conclusion

If even an unlabelled wrong analysis collapses discrimination, and a "this may be untrusted"
label is defeated by a persuasive wrong rationale, then **you cannot fix this by labelling,
de-authorizing, or warning the judge in the prompt.** That rules out the cheap prompt fixes and
leaves the structural one: **judge each source separately, compare mechanically, and route
disagreement to a deterministic verifier / second independent solver / human** — never let a
single model-facing channel silently decide.

## Caveats

- **reps=1, n=8** — CIs are wide; treat per-label magnitudes as indicative and only the large
  cross-model effects (1–4 above) as load-bearing. A confirmatory run wants reps≥3 and more items.
- Generated texts (cached in `provinj_texts.json`); single run; temp 0 (not deterministic across
  a hosted API); numeric domain; 0–100 judge scale.
- Discrimination can go negative (judge scores the wrong-but-matching candidate above the
  correct one) — several cells do, which is why injection effects are large.
