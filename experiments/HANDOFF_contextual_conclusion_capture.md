# Handoff - Contextual Conclusion Capture investigation

**Prepared:** 2026-07-14  
**Repository:** `petesherratt-collab/The-Generated-Trace-Leak-Harness`  
**Draft PR:** <https://github.com/petesherratt-collab/The-Generated-Trace-Leak-Harness/pull/1>  
**Publication branch:** `codex/contextual-conclusion-confirmation`  
**Publication worktree:** `C:\tmp\trace-leak-confirmatory`

This handoff is for continuing the judge-integrity investigation in a fresh context. It does
not replace the repository-root `HANDOFF.md`, which documents the original generated-trace
leak harness.

> **UPDATE 2026-07-17 — code-domain replication complete.** The bounded independent-domain
> replication (Python function judging, unit-test gold) ran as two frozen stages under
> [`PREREG_ccc_codedomain.md`](PREREG_ccc_codedomain.md) and is written up in
> [`results/FINDINGS_ccc_codedomain.md`](results/FINDINGS_ccc_codedomain.md), audited in
> [`results/ccc_code_offline_audit.txt`](results/ccc_code_offline_audit.txt). Result:
> **model-dependent CCC replication with strong but non-universal protection from context
> isolation — not a universally validated product safeguard.** Primary capture supported
> 4/5 (Stage 1); isolation and mechanical routing each supported 3/4, written verification
> 0/4 (Stage 2); Claude Haiku's numeric score-only non-compliance reversed (0/384 failures
> in code — captured +40 once measurable); gemini × verify-written accounted for 74/75 of
> all failures (fail-closed). Evidence commits: `1309d78` (S1), `c850083` (S2); do not
> rerun successful cells.

## Core finding so far

The confirmed phenomenon is **Contextual Conclusion Capture**: exposing an LLM judge to a
conflicting conclusion can reduce its ability to distinguish correct from incorrect candidate
solutions. A privileged solver label and a long persuasive rationale are not required.

In the completed frozen confirmation, the bare-conclusion score-only contrast was supported in
all four measurable models. Claude score-only was unmeasurable because of factor-correlated
format failures. Written verification strongly mitigated capture, but Llama retained large
residual capture.

The post-hoc paired-win interpretation defines:

`P(correct branch wins) = P(score_correct > score_wrong) + 0.5 P(tie)`.

Under score-only judging, a bare conflicting conclusion reduced that probability by 25.0
points for GPT-4o mini, 25.0 for Gemini, 30.2 for DeepSeek and 43.8 for Llama. Under written
verification, Llama still fell from 82.3% to 44.8%.

Do not describe this as proof of a subjective internal "crisis." The supported claim is
observable branch-selection instability caused by conflicting context.

## Completed confirmatory evidence

- Preregistration: `PREREG_contextual_conclusion_capture_confirmatory.md`
- Runner: `run_provenance_injection.py --confirmatory`
- Primary findings: `results/FINDINGS_contextual_conclusion_capture_confirmatory.md`
- Probability analysis: `analyze_confirmatory_choice_probability.py`
- Probability report: `results/confirmatory_choice_probability.md`
- Observations: `results/provinj_obs_confirmatory.jsonl`
- Prompt manifest: `results/provinj_prompts_confirmatory.jsonl`
- Metadata: `results/provinj_meta_confirmatory.json`
- Analysis log: `results/confirmatory_background.out.log`

Audit: 3,840 intended and unique cells; 3,622 successful; 218 unresolved; no duplicate
successful cells and no malformed JSONL. Missingness was concentrated in Claude score-only
and Gemini written verification. The raw evidence hashes are recorded in the findings report.

## Completed architecture experiment

The user explicitly requested the next causal test: determine whether architecture prevents
capture rather than merely prompting a contaminated judge to resist it.

Frozen files:

- `PREREG_contextual_capture_architecture.md`
- `run_architecture_capture.py`
- `analyze_architecture_capture.py`

Frozen design:

- 16 frozen items
- five models
- correct and wrong mirrored external references
- correct and wrong-matching candidates
- three repetitions
- schedule seed `984217603`
- 240 question-only routing solves
- 3,840 final judge cells

Architectures:

1. `contaminated_score_only`
2. `contaminated_verify_written`
3. `context_isolated_score_only`
4. `conflict_router`

Router policy is frozen. The same model first solves the question in a separate context. If its
parsed conclusion agrees with the external reference, the ordinary exposed score-only path is
used. If it disagrees or is unparseable, the reference is quarantined and a fresh judge sees
only the question and candidate under written verification. The solver transcript is never
shown to the final judge.

Frozen hashes:

- item definitions: `f9c756a17c5460a56ad9194e5c6d999919a6c85a4c68f82f57aa727ac269aa7c`
- effective stimuli: `16d7975e2e2b27c69520668904a6aa5051370727ec9918d218545b37721a5fe6`
- runner: `fe55cc676ec3672d2e2b365ee7a43be94c0c953e63fc646b4ee42fbaa686f3c0`
- analysis: `5a0872ed448935450daf28c8fece581bcbbe560a8cda41f6d5d5a04a91051ff4`

The run completed with 240/240 unique routing solves and 3,840/3,840 unique judge attempts.
There were 3,633 successful judge cells and 207 retained failures, with no malformed or
duplicate cells. See `results/FINDINGS_contextual_capture_architecture.md` for the fail-closed
analysis and evidence hashes.

The primary result is that context isolation improved wrong-reference discrimination in all
four models meeting the completeness rule. The conflict router improved it only for GPT and
Llama; Gemini and DeepSeek intervals included zero, and Claude did not meet the completeness
threshold. Therefore isolation is the strongest tested safeguard, while the frozen router is
not a universal solution.

## Benchmark-specific scope

This architecture experiment is benchmark-agnostic. It can support a causal claim on this
frozen item set, but it cannot establish that MT-Bench, AlpacaEval, Arena-Hard or another named
benchmark is affected. A named-benchmark test must reproduce its actual judge prompt,
reference visibility, ordering, candidate presentation, retry policy and aggregation.

If the real pipeline is unavailable, test only a declared reconstruction and do not name the
benchmark as tested.

## New strategic direction

The user proposed building an original benchmark with judge integrity designed in from the
start. This is likely more valuable than only auditing existing leaderboards. The proposed
design is in `BENCHMARK_BLUEPRINT_judge_integrity.md`.

The intended benchmark should make evaluator integrity a release gate, not a hidden assumption:
machine verification where possible; independent conclusion commitments; reference quarantine;
fresh conflict adjudication; mirrored integrity sentinels; complete prompt/evidence manifests;
and separate reporting of task performance, evaluator reliability and missingness.

## Operational warning

An earlier confirmatory launch accidentally created two writers and an interleaved malformed
row. Both processes were stopped, that partial evidence was preserved separately, and the
clean confirmatory run restarted from zero under an exclusive lock. This is why every future
run must enforce exactly one writer and why stale locks may be cleared only after process
verification.
