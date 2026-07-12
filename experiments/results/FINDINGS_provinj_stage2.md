# Findings — stage-2 preregistered provenance-injection run

**Date:** 2026-07-12 · **Harness:** `provenance_injection_harness.py` (rev3) · **Prereg:**
[`../PREREG_provenance.md`](../PREREG_provenance.md) · **Analysis log:**
[`run_provinj_stage2_analysis.txt`](run_provinj_stage2_analysis.txt) · **Evidence:**
`provinj_obs_stage2.jsonl` (5,313 rows, streamed; prompts resolvable via manifest)
· 8 code-verified items · 5 models · 2 protocols · 2 reps · scores 0–100

## Completeness first (per prereg policy)

**4,575 / 4,800 cells succeeded (95.3%)** across three resume segments (two container
restarts; streaming lost nothing). Missingness is **factor-correlated and disclosed**:

- **claude-haiku-4.5 × score_only: 208 missing cells (41% model failure rate).** The model
  *refuses the score-only format* — instructed to reply with only a JSON score, it begins a
  written verification instead and truncates. Retries at higher budgets fail the same way.
  Per prereg, **all claude score_only contrasts (and its protocol interactions) are
  unreliable (n=1–5) and are not interpreted.** Its verify_written side is complete (n=8).
- **gemini-2.5-flash × verify_written: 17 missing** (derivations exceeding even a 4,000-token
  recovery budget); its contrasts run at n=6–8, fail-closed.
- The other three models: ~0–1% failures.

**Claude's refusal is itself a finding:** one model spontaneously will not produce a bare
score without visible verification. Given score-only judging is the vulnerable configuration
throughout this work, that non-compliance is arguably protective behavior — but it makes the
model unbenchmarkable in the vulnerable mode rather than safe in it.

## Prereg scorecard (95% item-clustered CI excluding 0 in the predicted direction = supported)

### 1. Injection harm (wrong analysis, neutral label, vs no injection) — *predicted > 0*

| Model | score_only | verify_written |
|---|---|---|
| gpt-4o-mini | **+68.1 [+23.8, +111.3] ✅** | **+34.7 [+15.6, +53.8] ✅** |
| llama-3.3-70b | **+62.5 [+12.5, +100.0] ✅** | **+37.5 [+3.1, +71.9] ✅** |
| gemini-2.5-flash | +40.0 [−3.8, +83.8] ✗ (borderline) | −6.3 [−11.3, −1.3] ✗ (eliminated) |
| deepseek-chat | +39.4 [−1.9, +80.0] ✗ (borderline) | +6.3 [−17.5, +31.3] ✗ (eliminated) |
| claude-haiku | *(unreliable, n=2)* | −7.0 [−18.0, +2.0] ✗ |

**Supported for 2 of 4 measurable models in both protocols; directionally positive in
score_only for all four** (two just straddle 0). The core capture phenomenon replicates
under preregistration — a wrong analysis with a *neutral* label collapses discrimination
by ~40–68 points in score-only judging.

### 2. Provenance harm (solver label vs neutral label) — *predicted ≥ 0* → **NOT SUPPORTED anywhere**

Every solver-vs-neutral CI includes 0 (gpt +0.9, gemini +3.1, deepseek −8.8, claude(verify)
+3.1), and for **llama the sign significantly reverses** (−31.3 [−62.5, −6.3] score_only):
naming the source at all *reduced* capture relative to the bland "Additional Analysis"
heading. **The authority-label hypothesis fails under a clean identity-only cross: content,
not provenance identity, drives capture.** (This kills the "sealed solver badge is magic"
reading conclusively at this scale — consistent with the earlier exploratory hint, now with
the confound-free design.)

### 3. Rationale harm (full wrong rationale vs bare wrong answer, neutral label) — *predicted > 0* → **NOT SUPPORTED; often reversed**

score_only: gpt −8.1, gemini −21.9, deepseek −10.0, llama −25.0 (all CIs include 0 or lean
negative; llama's unlabelled variant −25.0 and gpt's −16.3 touch significance). Only
deepseek's verify_written shows a supported positive (+12.3 [+1.6, +25.4]).

**Interpretation — a genuine surprise:** in score-only judging, the **bare wrong answer
captures as much or more than the fully argued wrong analysis.** The capture is driven by
the *conflicting conclusion*, not the persuasive argument. This **refines the earlier
"persuasion dominates" claim**: what dominates is the presence of a contradicting answer;
elaborate reasoning adds little (and sometimes invites scrutiny that weakens it).

### 4. Protocol mitigation (diff-in-diff, score_only harm − verify_written harm) — *predicted > 0*

On injection harm: gemini **+46.3 [+3.8, +90.0] ✅**; gpt +33.4, deepseek +33.1, llama +25.0
(all positive, CIs include 0). **Directionally consistent for all four measurable models,
statistically supported for one.** Note the aligned pattern in contrast 1: verify_written
shrinks injection harm for every model (68→35, 63→38, 40→−6, 39→+6). So written verification
*reduces* capture but — for gpt and llama — **does not eliminate it** (both remain
significantly captured under verify_written). Capture is attenuated by protocol, not
abolished: partial mitigation, architectural residue.

## Exploratory (hypothesis-generating only)

- **A false "verified" claim increases capture** for deepseek (+26.9 [+4.4, +63.8] ✅) and
  directionally gemini (+18.8); tiny *negative* for gpt. **Skepticism claims help llama**
  strongly ("may contain errors" −50.0 [−87.5, −12.5]; "unverified" −31.3 — both supported).
  Reliability framing is a real lever for *some* models, in the sensible direction.
- **Sealed vs ordinary solver:** llama +12.5 [0, +31.3] borderline; others ≈ 0. No general
  "sealed" premium.
- **Header/presentation effects:** small and mixed (gpt +4.4 supported in one cell; gemini
  verify +12.9 in another) — minor compared to injection itself.

## What stage 2 changes about the story

1. **The capture phenomenon is real and preregistration-robust** (contrast 1), and the
   verify protocol **attenuates but does not abolish it** (contrast 4 + gpt/llama's
   still-significant verify-mode harm). The architectural conclusion stands on firmer
   ground: protocol-level mitigation is partial, so conflict-routing + independent
   verification remains the only complete fix.
2. **Provenance identity is exonerated** (contrast 2). Labels don't carry the effect;
   the conflicting content does. Prompt-level "don't trust the solver" interventions were
   already shown weak; now we know even the *label itself* isn't the mechanism.
3. **The mechanism sharpens further** (contrast 3): it's the *conflicting conclusion*, not
   the persuasive rationale. A bare contradicting number captures score-only judges as
   effectively as a full argument. "Persuasion dominates" → "**conclusion-conflict
   dominates**."
4. **Model heterogeneity is large and behavioral**: claude refuses the vulnerable protocol
   outright; llama is spooked by any named source and calmed by skepticism claims; deepseek
   is the most reliability-claim-sensitive. Judge-integrity properties do not transfer
   across models.

## Caveats

- n = 8 items, one numeric domain, reps = 2, single run; several primary CIs are wide and
  two borderline calls (gemini/deepseek injection in score_only) would likely resolve with
  the prereg's confirmatory stage (≥16 items, ≥3 reps).
- Claude's score_only column is missing-not-at-random (its refusal); per prereg it is
  excluded, not imputed. Gemini's verify column runs fail-closed at n=6–8.
- Injected/candidate texts are model-generated (frozen in `provinj_texts.json`); Phase-1
  overlap audit: word-4gram Jaccard 0.083 (agreement is conclusion-level, not lexical).
- Scores are coarse (many 0/100 saturations); treat magnitudes as indicative, directions
  and supported/not-supported calls as the result.
