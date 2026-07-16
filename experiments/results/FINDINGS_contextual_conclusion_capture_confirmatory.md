# Findings - Contextual Conclusion Capture confirmatory run

**Run completed:** 2026-07-14<br>
**Frozen design:** 16 items, 5 models, 4 conditions, 2 candidate types, 2 protocols,
3 repetitions (3,840 intended judge cells)<br>
**Preregistration:**
[`../PREREG_contextual_conclusion_capture_confirmatory.md`](../PREREG_contextual_conclusion_capture_confirmatory.md)<br>
**Analysis log:** [`confirmatory_background.out.log`](confirmatory_background.out.log)<br>
**Raw observations:** [`provinj_obs_confirmatory.jsonl`](provinj_obs_confirmatory.jsonl)<br>
**Recorded code revision:** `484313cf82921512d83b8ee1580a77cea0969442`<br>
**Schedule seed:** `731942587`

## Executive result

The confirmatory run supports **Contextual Conclusion Capture**: merely placing a conflicting
conclusion in the evaluation context substantially reduced a score-only judge's ability to
distinguish correct from incorrect candidates. The direct preregistered bare-conclusion test
was supported in **all four measurable models**. Claude Haiku was not measurable for this
contrast because only 4 of 16 items satisfied the frozen three-repetition completeness rule.

The result also sharpens the mechanism. In score-only judging, a solver label did not add
capture in any measurable model, and a full wrong rationale did not add consistent harm over
the bare wrong answer. A conflicting conclusion was sufficient. Written verification strongly
mitigated bare-conclusion capture in all four measurable models, but did not eliminate it for
Llama. This supports explicit verification, context separation, and conflict routing as
stronger safeguards than unverified score-only judging; it does not prove that any one of
those safeguards is uniquely complete.

## Completeness and evidence audit

The clean run contains **3,840 stored rows for 3,840 unique intended cells**. There are no
duplicate cells, duplicate successful observations, or malformed JSONL rows.

| Measure | Count |
|---|---:|
| Intended and attempted cells | 3,840 |
| Successful observations | 3,622 (94.3%) |
| Failed attempts / unresolved cells | 218 (5.7%) |
| Cells with multiple attempts | 0 |
| Cells with multiple successes | 0 |
| Maximum attempts for one cell | 1 |

All 218 failures were parser failures caused by responses that did not contain the requested
score JSON object. Missingness was strongly factor-correlated:

| Model | score_only failures | verify_written failures | Total successes | Total failure rate |
|---|---:|---:|---:|---:|
| GPT-4o mini | 0 / 384 | 0 / 384 | 768 / 768 | 0.0% |
| Claude Haiku 4.5 | 162 / 384 | 0 / 384 | 606 / 768 | 21.1% |
| Gemini 2.5 Flash | 0 / 384 | 56 / 384 | 712 / 768 | 7.3% |
| DeepSeek Chat | 0 / 384 | 0 / 384 | 768 / 768 | 0.0% |
| Llama 3.3 70B Instruct | 0 / 384 | 0 / 384 | 768 / 768 | 0.0% |

Claude failed on 42.2% of its score-only cells but none of its written-verification cells.
Gemini failed on 14.6% of its written-verification cells but none of its score-only cells.
This missingness is plausibly related to protocol compliance and response length, so it is not
assumed missing at random. No values are imputed. An item enters a contrast only if all three
repetitions of every required cell succeeded. Per preregistration, a directional effect is
called supported only if its item-bootstrap 95% interval excludes zero and at least 12 of 16
items are complete.

Before this clean run, an operational launch error briefly created two concurrent writers.
Both were stopped, their partial files were preserved separately, and none of those rows enter
this analysis. The final dataset was restarted from zero under an exclusive single-writer lock.

## Preregistered scorecard

Direction convention: `harm = discrimination(no injection) - discrimination(injection)`.
Positive values mean worse correct-versus-incorrect discrimination and therefore more capture.
Effects are score points with item-clustered bootstrap 95% intervals.

### 1. Bare conflicting conclusion under score-only judging - predicted positive

This is the direct Contextual Conclusion Capture test.

| Model | Complete items | Harm [95% CI] | Preregistered call |
|---|---:|---:|---|
| GPT-4o mini | 16 | **+55.10 [+21.77, +90.62]** | **Supported** |
| Claude Haiku 4.5 | 4 | +111.25 [+103.75, +117.50] | **Unmeasurable** (below n=12 floor) |
| Gemini 2.5 Flash | 16 | **+39.06 [+9.90, +74.58]** | **Supported** |
| DeepSeek Chat | 16 | **+47.83 [+32.67, +66.79]** | **Supported** |
| Llama 3.3 70B | 16 | **+87.50 [+62.50, +112.50]** | **Supported** |

**Result:** supported in 4 of 4 measurable models. The smallest measurable estimate was a
39-point loss of discrimination; the largest was 88 points. Claude's large estimate is not a
confirmatory result because its four complete items fall far below the frozen completeness
threshold.

### 2. Full wrong rationale under score-only judging - predicted positive

| Model | Complete items | Harm [95% CI] | Preregistered call |
|---|---:|---:|---|
| GPT-4o mini | 16 | **+55.42 [+21.88, +90.83]** | **Supported** |
| Claude Haiku 4.5 | 3 | +36.67 [-15.00, +100.00] | **Unmeasurable** |
| Gemini 2.5 Flash | 16 | **+32.81 [+9.48, +58.02]** | **Supported** |
| DeepSeek Chat | 16 | **+38.04 [+16.38, +61.25]** | **Supported** |
| Llama 3.3 70B | 16 | **+85.42 [+54.17, +114.58]** | **Supported** |

**Result:** the Stage 2 full-analysis effect replicated on the expanded item set in all four
measurable models.

### 3. Written-verification mitigation of bare-conclusion harm - predicted positive

This difference-in-differences estimate is
`harm(score_only) - harm(verify_written)`. Positive values mean written verification reduced
capture.

| Model | Complete items | Mitigation [95% CI] | Preregistered call |
|---|---:|---:|---|
| GPT-4o mini | 16 | **+43.46 [+10.46, +77.62]** | **Supported** |
| Claude Haiku 4.5 | 4 | +117.33 [+106.67, +128.00] | **Unmeasurable** |
| Gemini 2.5 Flash | 12 | **+61.39 [+24.44, +102.50]** | **Supported** |
| DeepSeek Chat | 16 | **+56.06 [+38.79, +74.29]** | **Supported** |
| Llama 3.3 70B | 16 | **+28.33 [+3.54, +51.46]** | **Supported** |

**Result:** supported in all four measurable models. This is stronger and more consistent
evidence for protocol mitigation than Stage 2 produced.

### 4. Residual capture under written verification

| Model | Bare conclusion harm [95% CI] | Full rationale harm [95% CI] | Interpretation |
|---|---:|---:|---|
| GPT-4o mini | +11.65 [-0.46, +23.94], n=16 | **+21.44 [+8.40, +35.10]**, n=16 | Bare residual not supported; full residual supported |
| Claude Haiku 4.5 | -2.21 [-11.33, +5.77], n=16 | -10.33 [-18.85, -2.13], n=16 | No positive residual capture |
| Gemini 2.5 Flash | -7.64 [-14.44, -0.14], n=12 | -14.26 [-20.56, -8.15], n=9 | Bare effect reverses; full contrast below completeness floor |
| DeepSeek Chat | -8.23 [-18.75, +1.15], n=16 | +7.81 [-4.69, +20.73], n=16 | No supported residual capture |
| Llama 3.3 70B | **+59.17 [+35.83, +85.42]**, n=16 | **+67.94 [+31.58, +103.50]**, n=16 | Large residual capture remains |

The preregistered expectation of residual capture for GPT-4o mini and Llama is partially
supported: both Llama contrasts and GPT's full-rationale contrast are positive and supported;
GPT's bare-conclusion interval narrowly includes zero. Written verification is therefore a
strong mitigation, not a universal elimination.

## Exploratory probability view: which branch wins?

The preregistered analysis measures loss of score discrimination. A post-hoc paired-choice
analysis translates the same frozen scores into the empirical probability that the correct
candidate beats the matched wrong candidate:

\[
P(correct\ branch\ wins) = P(S_{correct} > S_{wrong})
+ \frac{1}{2}P(S_{correct} = S_{wrong}).
\]

Probabilistic capture is the drop in that quantity between no injection and a conflicting
conclusion. Under score-only judging, the bare conclusion reduced the correct-branch win rate
from 61.5% to 36.5% for GPT, 78.1% to 53.1% for Gemini, 71.9% to 41.7% for DeepSeek, and 71.9%
to 28.1% for Llama. Written verification removed the measurable bare-conclusion drop for GPT,
Gemini, and DeepSeek, while Llama still fell from 82.3% to 44.8%.

These are paired-win frequencies over the frozen items, not calibrated internal truth beliefs.
The analysis was not preregistered and therefore supports interpretation rather than a new
confirmatory claim. Full methods, intervals, and all model/protocol cells are in
[`confirmatory_choice_probability.md`](confirmatory_choice_probability.md).

## Mechanism checks

### Provenance increment: solver label versus neutral label

Under score-only judging, the solver label added no positive capture in any measurable model:
GPT -0.42, Gemini -5.94, DeepSeek +1.67, and Llama **-22.92 [-43.75, -4.17]**. Only Llama's
interval excluded zero, and it ran in the opposite direction: the solver label reduced capture.
Claude was unmeasurable (n=4).

Under written verification, GPT, Claude, and DeepSeek were null; Llama again showed a supported
reduction (-38.67 [-61.12, -19.42]). Gemini's +9.26 estimate used only 9 complete items and is
below the preregistered completeness floor.

**Interpretation:** the data do not support provenance identity as the general driver. This
does not establish equivalence or prove labels can never matter; it shows that a privileged
solver label was unnecessary for the confirmed effect and did not increase score-only capture
in this design.

### Rationale increment: full rationale versus bare conclusion

The score-only rationale increments were GPT +0.31, Gemini -6.25, DeepSeek -9.79, and Llama
-2.08; every interval included zero. Claude was unmeasurable (n=2). Under written verification,
only DeepSeek showed a supported positive increment (+16.04 [+2.81, +29.69]); the others were
null or below the completeness floor.

**Interpretation:** a detailed persuasive rationale was not required for capture. The bare
conflicting conclusion produced approximately the same score-only harm as the full rationale
for GPT and Llama, and numerically more harm for Gemini and DeepSeek. The experiment supports
sufficiency of the conclusion conflict, not universal irrelevance of rationales.

## What the confirmation establishes

1. **Contextual Conclusion Capture is confirmed across the four measurable score-only
   judges.** A neutrally presented wrong answer alone caused a large, supported loss of
   candidate discrimination.
2. **The conflicting conclusion is sufficient.** Neither a solver identity nor a long wrong
   rationale was needed to produce the effect.
3. **Written verification is a robust mitigation.** It significantly reduced bare-conclusion
   harm in every measurable model, but Llama retained large residual capture.
4. **Judge behavior is heterogeneous.** Claude's score-only format non-compliance and Gemini's
   written-verification failures prevent simple cross-model safety rankings.
5. **The architectural claim remains bounded.** These results support separating untrusted
   conclusions from judging context, explicitly routing conflicts, and requiring independent
   verification. They do not demonstrate that conflict routing is the only complete remedy or
   directly test a production architecture.

## Limitations

- The domain is 16 numerical/combinatorial questions, not open-ended evaluation.
- Scores are coarse and often near 0 or 100; magnitudes should be treated as indicative while
  directions and preregistered support calls are primary.
- Claude score-only and Gemini verify-written missingness is factor-correlated and plausibly
  missing-not-at-random. The fail-closed rule protects individual contrasts but cannot recover
  representativeness for unavailable items.
- No failed cell was retried in the clean run. The 218 failures remain unresolved and are fully
  disclosed rather than silently replaced.
- The eight new items use declared human-audited overrides for the candidate and injection
  fields after raw generation repeatedly produced incoherent forced-decoy rationales. Raw
  generations and overrides are both preserved and hashed.
- Injected-wrong and matching-wrong texts had low question-excluded word-4gram overlap
  (mean Jaccard 0.045), making simple lexical copying an unlikely explanation for agreement at
  the conclusion level.
- Confidence intervals are item-clustered bootstrap intervals over at most 16 items; estimates
  remain sensitive to item-domain expansion.

## Reproducibility and integrity

- Item-definition SHA-256:
  `f9c756a17c5460a56ad9194e5c6d999919a6c85a4c68f82f57aa727ac269aa7c`
- Effective-stimulus SHA-256:
  `16d7975e2e2b27c69520668904a6aa5051370727ec9918d218545b37721a5fe6`
- Observation JSONL SHA-256:
  `6fe88a462cc4b7b090edcf39ccafeb52c30a06c854a2bfbf0b1f701cfe758317`
- Prompt manifest SHA-256:
  `7dc21ec59fd0b3d68245a86a1dcb03eaeae753d47f97726ff33e9b77315e4aba`
- Metadata SHA-256:
  `692ea8e4313ec513d6d73a87b57a89eb9f682d22cfaaeccd185c8363dc359ca0`
- Analysis-log SHA-256:
  `07e7007c991d31fd7b09931b2b0414011c7790adf37705fdbd77dd5343564787`

The raw observation and prompt files were not modified in preparing this report.
