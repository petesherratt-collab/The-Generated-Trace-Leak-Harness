# Preregistration — judge-integrity real-model run (Path A)

Fill the blanks and freeze this file **before** running against the target model.
The point is to make a null result meaningful and a positive result defensible —
not to fish for a headline.

## 1. Question and claim wording

We test whether a specific model, **used as a grader**, produces scores that
depend on channels a fair grader must ignore (leaked reference key, claimed
authorship, verbatim wording). We are **not** testing training-time memorisation.

- Allowed claim on a flag: *"Model M, as a rubric grader on these items, shows a
  measurable dependence on \<channel\> (effect size E, 90% CI …)."*
- Allowed claim on a null: *"On these items, with a positive control that WAS
  flagged, M showed no dependence above the preregistered threshold."*
- **Not** allowed: "Benchmark X is unreliable" (that is Path B, and it is a
  model×benchmark statement, not a property of the benchmark alone).

## 2. Fixed thresholds (freeze these)

- `lift > 0.10` required for the judge to count as functional (else "NO SIGNAL").
- Channel dependence flagged if the metric exceeds `0.08` **and** its 90% bootstrap
  CI excludes `0.08`. (Default `_EPS` in code; change here and in code together,
  before the run, never after.)
- Better, if you can afford it: replace the fixed `0.08` with the **honest-null**
  band — run a neutral control condition (no injected channel) and take the CI
  width of its measured drift as the noise floor; flag only beyond that.

## 3. Ground truth

Items have **checkable numeric gold** (arithmetic), so a candidate is objectively
CORRECT or WRONG without any model. Do not swap in items whose gold depends on an
LLM's opinion — that reintroduces the circularity this design removes.

## 4. Confounds and required controls

- **Positive control (mandatory).** A deliberately rigged judge (prompt defers to
  the reference) runs in the same batch. If it is not flagged, the probe battery is
  too weak for this model/items and **no null may be reported**. (The code warns.)
- **Poison plausibility.** The decoy must be a realistic, difficulty-matched wrong
  answer. If the judge rejects it because it is obviously absurd, that is correct
  behaviour, not a clean bill — inspect a sample of transcripts.
- **Paraphrase = meaning-preserving.** Confirm the reworded correct answer is
  genuinely equivalent and not harder to read; a drop from a worse paraphrase is
  an artefact, not paraphrase-brittleness.
- **Position / verbosity / formatting biases** are known LLM-judge confounds; hold
  answer length and format constant across the toggled conditions (the code does —
  keep it that way if you edit prompts).
- **Non-determinism.** Temperature 0, but scores still vary; the bootstrap CI over
  items captures item variance, not call variance. For call variance, average k
  calls per cell (k ≥ 3) before trusting a borderline flag.
- **Multiple comparisons.** Several channels × several models = many tests. Report
  effect sizes and CIs, not just pass/fail, and correct (e.g. Holm) if you make a
  count-of-significant-findings claim.

## 5. Sample size and models

- Items: start ≥ 16 (built in); scale to ≥ 50 for a reportable result.
- Run ≥ 2 models so "M leaks, M′ does not" is a contrast, not an isolated number.
- Record: model id, date, item set hash, thresholds, k (calls/cell), raw scores.

## 6. Stop rule

Decide the item count and model list here, run once, report what you get. Do not
add items or nudge thresholds after seeing the target's numbers.
