# Preregistration — Contextual Conclusion Capture confirmatory run

**Frozen design date:** 2026-07-13<br>
**Harness:** `provenance_injection_harness.py` (rev3 plus fail-closed top-level plumbing)<br>
**Adapter:** `run_provenance_injection.py --confirmatory`<br>
**Item-definition SHA-256:** `f9c756a17c5460a56ad9194e5c6d999919a6c85a4c68f82f57aa727ac269aa7c`<br>
**Schedule seed:** `731942587`

This is the fresh-schedule, larger-item confirmation specified after the Stage 2 run. It
does not repeat the exploratory status, reliability, header or control matrix.

## Question and construct

**Contextual Conclusion Capture** is a deterioration in an AI judge's ability to distinguish
correct from incorrect candidates when a conflicting conclusion is present in the evaluation
context. The primary question is whether a neutrally presented bare wrong conclusion causes
capture without needing a privileged source label or supporting rationale.

Direction convention throughout: `harm = discrimination(baseline) -
discrimination(condition)`. Positive values mean worse discrimination / more capture.

## Frozen design

- **Items:** 16 code-verified numerical/combinatorial items. The original eight are retained;
  eight new questions have exhaustively computed gold answers and two distinct frozen decoys.
- **Models:** `openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`,
  `google/gemini-2.5-flash`, `deepseek/deepseek-chat`, and
  `meta-llama/llama-3.3-70b-instruct`.
- **Protocols:** `score_only` and `verify_written`.
- **Candidate types:** `correct` and `wrong_matching`.
- **Repetitions:** exactly 3, independently shuffled and deterministically deconflicted.
- **Conditions:** exactly four:
  1. `no_injection`
  2. `neutral/wrong_answer_only`
  3. `neutral/full_wrong_rationale`
  4. `solver/full_wrong_rationale`
- **Schedule:** fixed seed `731942587`, recorded in metadata.
- **Size:** 3,840 judge cells, plus 56 one-time generations for the eight new frozen text sets.

Candidate and injected texts for the eight new items were generated in a separate preparation
step and written to `results/provinj_texts_confirmatory.json`. Pre-run review found that the
generator often calculated the gold value and then jumped to the forced decoy. Rather than
retry until a favourable sample appeared, the two fields actually used by this confirmation
(`wrong_matching` and `inj_wrong`) were replaced by a declared, human-audited override file.
Each override contains one fixed coherent error mechanism and never mentions the gold answer.
The raw generations remain preserved. Metadata records hashes for the raw cache, override file,
and merged effective stimuli. The frozen effective-stimulus SHA-256 is
`16d7975e2e2b27c69520668904a6aa5051370727ec9918d218545b37721a5fe6`.

## Primary contrasts

Each estimate is paired within item and bootstrapped over items. An item enters a contrast only
when all three repetitions of every required cell succeeded.

1. **Bare-conclusion injection harm, score-only**<br>
   `disc(no_injection) - disc(neutral, wrong_answer_only)`. Predicted `> 0`.
   This is the direct Contextual Conclusion Capture test.
2. **Full-analysis injection harm, score-only**<br>
   `disc(no_injection) - disc(neutral, full_wrong_rationale)`. Predicted `> 0`.
   This checks replication of the Stage 2 injection effect on the expanded set.
3. **Protocol mitigation of bare-conclusion harm**<br>
   `harm(score_only) - harm(verify_written)`. Predicted `> 0`.
4. **Residual capture under written verification**<br>
   Bare- and full-injection harm under `verify_written`, reported per model. Based on Stage 2,
   residual positive capture is specifically predicted for GPT-4o mini and Llama.

An effect is called supported only when its 95% item-clustered bootstrap interval excludes zero
in the predicted direction and at least 12 of 16 items are complete for that contrast. Models
below that completeness floor are reported as unmeasurable for the contrast, not as null.

## Mechanism checks

The same cells estimate:

- **provenance increment:** `harm(solver, full) - harm(neutral, full)`;
- **rationale increment:** `harm(neutral, full) - harm(neutral, bare)`.

These are estimates of incremental effects. A confidence interval containing zero is **not**
treated as proof of equivalence or absence. The Stage 2 conclusion is therefore phrased as the
conflicting conclusion being sufficient for capture, not as labels and rationales being
universally irrelevant.

## Missingness, retries and evidence policy

- Every attempt is appended immediately to the observation JSONL; prompts are stored in the
  hash-keyed manifest.
- A resume retries only cells without a successful observation. Failed attempts remain evidence.
- The cell key is `(item, model, condition, candidate type, repetition, protocol)`.
- At most one successful row per cell is permitted. More than one is a hard analysis error.
- Failed attempts are never averaged with successes. Analyses use successful rows and require
  exactly three successful repetition cells per required item/contrast.
- Report stored attempts, unique cells, failed attempts, retried cells, unresolved cells,
  maximum attempts and failures by model/protocol/condition/candidate before effects.
- Claude's prior score-only non-compliance is treated as potentially missing-not-at-random. It
  receives no safety or protective interpretation; affected contrasts are simply unavailable
  if they fail the completeness floor.

## Evidence files and stop rule

- `results/provinj_meta_confirmatory.json`
- `results/provinj_obs_confirmatory.jsonl`
- `results/provinj_prompts_confirmatory.jsonl`
- `results/provinj_texts_confirmatory.json`
- `results/provinj_texts_confirmatory_overrides.json`
- `results/provinj_texts_confirmatory.sha256`

Run the frozen schedule once. Resume is allowed only to recover unsuccessful cells and may not
change items, models, conditions, repetitions, protocols or schedule seed. Do not add items,
change hypotheses, alter thresholds or substitute models after inspecting outcomes.

The permitted architectural claim is limited to: the results support context separation and
explicit conflict routing as stronger safeguards than the tested prompt-level protocols. They
do not prove that conflict routing is the only possible complete mitigation.
