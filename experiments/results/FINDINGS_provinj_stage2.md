# Findings — stage-2 preregistered run: Contextual Conclusion Capture

> **Central concept (renamed after this run).** The earlier "relocated authority channel"
> hypothesis is falsified in its mechanism. What the data support is **Contextual
> Conclusion Capture**: *a failure mode in which an AI judge's ability to distinguish
> correct from incorrect candidates deteriorates merely because a conflicting conclusion
> is present in its evaluation context, independent of that conclusion's stated authority
> or supporting rationale.* The judge does not need to believe the foreign source is
> authoritative; it may simply be unable to maintain an independent verdict once another
> plausible final answer is present. Retired: "the sealed solver becomes the new answer
> key." Replacement: "the solver's conclusion becomes a competing answer signal, whether
> or not the solver is treated as authoritative."

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

**Claude's non-compliance is itself a finding, stated without attributing motive:** Claude
Haiku was largely non-compliant with the vulnerable score-only protocol, preventing reliable
measurement in that condition. Instructed to return a bare JSON score, it instead begins a
written verification and truncates. We do not infer intent from this — the honest description
is non-compliance that makes the model *unbenchmarkable in the vulnerable mode*, not
demonstrably *safe* in it. Its verify_written side is complete and is interpreted normally.

### Row accounting and deduplication

The evidence file `provinj_obs_stage2.jsonl` holds **5,313 stored observations**, which is
larger than the 4,800 intended cells because it records retry and cross-restart recovery
attempts, not just final results. The reconciliation is:

- **4,800** unique intended cells (8 items × 5 models × 2 protocols × conditions × candidates × 2 reps, per the schedule).
- **4,575** cells with a successful final observation (the analysed set).
- **738** failed attempts (truncations, retries, recovery passes) also streamed to the log.
- **0** cells with more than one successful row.

Deduplication key: `(item, model, condition, candidate, rep, protocol)`. **Only the final
successful attempt per cell enters analysis**; failed attempts are retained in the log for
audit but excluded from every estimate. (5,313 stored − 738 failed attempts = 4,575 analysed
successes; the 225-cell gap to 4,800 is the fail-closed missingness catalogued above, almost
all claude × score_only and gemini × verify_written.)

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
   ground, stated within what was actually tested: written verification reduced capture in
   every measurable model and significantly so for gemini, but gpt-4o-mini and llama
   remained captured. So **the results support conflict routing and context separation as
   stronger safeguards than prompt-level warnings or written-verification instructions
   alone.** They do *not* prove no other architecture could solve it — only that the
   prompt-level and verification mitigations we tested are incomplete.
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
