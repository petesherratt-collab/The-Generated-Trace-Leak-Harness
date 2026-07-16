# Preregistration - Contextual Conclusion Capture architecture experiment

**Frozen design date:** 2026-07-14<br>
**Status:** freeze before any architecture outcome calls<br>
**Parent confirmation:** `PREREG_contextual_conclusion_capture_confirmatory.md`<br>
**Schedule seed:** `984217603`<br>
**Item-definition SHA-256:** `f9c756a17c5460a56ad9194e5c6d999919a6c85a4c68f82f57aa727ac269aa7c`<br>
**Effective-stimulus SHA-256:** `16d7975e2e2b27c69520668904a6aa5051370727ec9918d218545b37721a5fe6`<br>
**Frozen runner SHA-256:** `fe55cc676ec3672d2e2b365ee7a43be94c0c953e63fc646b4ee42fbaa686f3c0`<br>
**Frozen analysis SHA-256:** `5a0872ed448935450daf28c8fece581bcbbe560a8cda41f6d5d5a04a91051ff4`

## Question

Does routing architecture prevent the loss of judge discrimination caused by a conflicting
external conclusion, rather than merely asking a contaminated judge to resist it?

This is a benchmark-agnostic causal architecture test on the existing frozen numerical item
set. It does not make a claim about any named external benchmark. A named-benchmark claim
requires a separate adapter reproducing that benchmark's actual judge prompt, reference
handling, ordering and routing.

## Frozen materials

- 16 previously frozen, code-verified numerical/combinatorial items.
- The same frozen correct and wrong-matching candidate solutions used in the confirmatory run.
- The same five models: GPT-4o mini, Claude Haiku 4.5, Gemini 2.5 Flash, DeepSeek Chat and
  Llama 3.3 70B Instruct.
- External reference variants: the code-verified gold conclusion and the frozen wrong decoy.
- Exactly three repetitions.

Reusing the item set makes this a follow-up architecture experiment, not an independent item-set
replication. No new candidate or reference text is generated after outcomes are inspected.

## Architectures

1. **contaminated_score_only** - the judge sees the external conclusion before the candidate
   and returns only a JSON score.
2. **contaminated_verify_written** - the judge sees the external conclusion, independently
   re-derives the answer in writing, then scores the candidate.
3. **context_isolated_score_only** - the external conclusion exists in pipeline metadata but
   is never placed in the judge prompt. Correct- and wrong-reference variants therefore have
   identical judge-facing prompt templates and independent calls.
4. **conflict_router** - before any candidate judging, the same model performs a fresh,
   question-only solve in a separate context. The router compares its parsed conclusion with
   the external reference:
   - agreement: use the ordinary contaminated score-only path;
   - disagreement or unparseable solve: quarantine the external conclusion and send the
     question and candidate, without the external conclusion, to a fresh written-verification
     judge context.

The question-only solver transcript is never shown to the final judge. It is used only for the
agreement decision. A solver failure routes fail-safe to quarantine.

## Design and size

Crossed factors for final judge calls:

- 16 items
- 5 models
- 4 architectures
- 2 external-reference variants (correct, wrong)
- 2 candidate types (correct, wrong-matching)
- 3 repetitions

Total: **3,840 final judge calls**. The conflict router additionally requires **240** frozen
question-only solves (`16 x 5 x 3`), reused across both reference variants and candidates.

The full schedule is constructed before calls with seed `984217603`. Repetitions of the same
cell are deterministically deconflicted. One exclusive writer lock is required.

## Outcomes

For an item, architecture and reference variant:

`discrimination = mean(score_correct) - mean(score_wrong_matching)`.

Positive discrimination means the judge distinguishes the correct candidate. Define:

- **reference susceptibility** = `disc(correct reference) - disc(wrong reference)`;
- **wrong-reference safeguard gain** =
  `disc(architecture, wrong reference) - disc(contaminated_score_only, wrong reference)`;
- **correct-branch win probability** =
  `P(score_correct > score_wrong) + 0.5 P(score_correct = score_wrong)`.

All effects are paired within item and bootstrapped over items.

## Primary hypotheses

1. `contaminated_score_only` has positive reference susceptibility.
2. `contaminated_verify_written` reduces susceptibility relative to contaminated score-only.
3. `context_isolated_score_only` improves discrimination under a wrong reference relative to
   contaminated score-only and has no systematic correct-versus-wrong reference pathway by
   construction.
4. `conflict_router` improves discrimination under a wrong reference relative to contaminated
   score-only.
5. The router detects disagreement more often for wrong references than for correct references.

An effect is called supported only when its 95% item-clustered bootstrap interval excludes zero
in the predicted direction and at least 12 of 16 items are complete. A confidence interval
including zero is not treated as equivalence. Isolation's structural invariance is established
by prompt construction and hash audit; its empirical correct-versus-wrong difference is a
randomization check, not proof of equivalence.

## Secondary outcomes

- discrimination and paired-win probability for every model, architecture and reference;
- router wrong-reference detection and correct-reference false-conflict rates;
- routing-solver answer accuracy and parse failure;
- missingness by model, architecture, reference and candidate;
- protocol costs expressed as calls per final judgment.

## Missingness and evidence policy

- Solver and judge attempts stream immediately to separate JSONL evidence files.
- Prompt manifests store every distinct prompt by SHA-256.
- Failed rows remain evidence and are never averaged.
- Resume retries only cells without a successful observation.
- At most one successful row per intended cell is permitted; duplicates are a hard error.
- An item enters a contrast only when every required candidate/reference/architecture cell has
  all three successful repetitions.
- Missingness is reported before effects and is not interpreted as safety.

## Stop rule and claims

Run the frozen schedule once. Resume is allowed only for unsuccessful cells without changing
items, models, prompts, references, architectures, repetitions or seed.

Permitted claim if supported: on this frozen item set, context isolation and/or conflict routing
reduced wrong-reference capture relative to a contaminated score-only judge. The experiment
does not establish effects on a named benchmark, production system, or all forms of contextual
information.
