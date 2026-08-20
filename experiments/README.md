# experiments/ — exploratory ports of the leak-harness method

These are **proofs of concept**, not the canonical instrument. They reuse the
method proven in the root harness (blind mirrored controls + honest/adversarial
actors as runnable code) in a domain that is easier to explain to a non-expert.

## `judge_integrity_poc.py` — "is the judge marking the work, or cheating?"

A legible port of the leak-harness idea to **AI evaluation / benchmark integrity**.
Same one question, new clothes:

> Is the evaluator scoring the submitted work, or getting the expected answer
> through another route — a leaked answer key, benchmark recognition, who wrote
> the answer, or the answer's wording?

A trustworthy judge's score depends **only** on the sanctioned evidence (the
candidate answer read against the rubric). The harness measures its dependence on
each contaminating channel and flags any that moves the score.

**Mapping** (leak harness → judge integrity):

| Leak harness            | Judge equivalent                                  |
|-------------------------|---------------------------------------------------|
| true broken edge `T`    | hidden gold answer `G`                             |
| decoy edge `D`          | a plausible **wrong** reference `D`               |
| observation channel     | candidate answer + rubric (the only fair input)   |
| side channel            | leaked key / item id / author / verbatim wording  |
| trace generator         | the judge (scoring model)                         |
| honest reader           | judge using only the answer + rubric              |
| cheater                 | judge exploiting a hidden/irrelevant channel      |

**Two probe families:**

1. **Blind mirrored controls** for the answer-key channel — the direct analog of
   the parent harness. `honest / collude / decouple / poison` conditions blind the
   judge to which reference is the truth; an honest judge follows the *answer* (high
   on `honest`+`poison`), a key-leaker follows the *reference* (marks a correct
   answer **down** on `poison`, where the leaked key is wrong).
2. **Hold-evidence-fixed toggles** for the other channels — keep the answer's true
   quality fixed and flip one irrelevant field (item recognised? claimed author?
   verbatim vs paraphrased?). A fair score doesn't move; a contaminated one does.
   (These catch benchmark-recognition and self-preference, which the mirrored
   controls alone miss — a useful lesson in the run.)

**Run it** (pure Python 3.10+, no deps, no network, deterministic):

```bash
python3 experiments/judge_integrity_poc.py
```

Expected: `HonestJudge` → PASS; `AnswerKeyLeaker`, `BenchmarkRecogniser`,
`SelfPreferrer`, `ParaphraseBrittle` each flagged by their own probe. The file
self-checks these on every run.

**Status / honesty.** It is a *simulation* proving the **method** — the honest and
adversarial judges are Python classes, exactly as the root harness simulates its
generators. Cutoffs are stipulated, not derived. It cannot prove a real model never
memorised a benchmark in pretraining (memorisation is not a toggle-able side
channel), though it can flag behaviour that collapses under recognition/paraphrase
transforms.

## `judge_integrity_real.py` — the same probes, wired for a real model

The next step up: run Path A (judge integrity) against an **actual model used as a
grader**. It reuses `evaluate()`/`verdict()` from the PoC unchanged; only the scores
become real. Two design choices make a result credible:

- **Checkable gold.** Items are arithmetic word problems with unambiguous numeric
  answers, so a candidate's true quality is known *without* any model — the
  ground-truth signal never depends on the model under test.
- **Positive control.** A deliberately rigged judge (its prompt defers to the
  reference) runs in the same batch. A null on the real judge only means something
  if the harness flags the rigged one — that proves the probes are sensitive.

Runs via **OpenRouter** (one key, many models, OpenAI-compatible) so multi-model
comparison — which the method wants — is a single flag.

```bash
# Real run (needs an OpenRouter key + egress to openrouter.ai):
export OPENROUTER_API_KEY=sk-or-...
python3 experiments/judge_integrity_real.py \
    --models openai/gpt-4o-mini,anthropic/claude-haiku-4.5 --items 16
python3 experiments/judge_integrity_real.py ... --reason   # let the judge reason first

# No key: a clearly-labelled LOCAL WIRING CHECK (stub scorers, not a finding):
python3 experiments/judge_integrity_real.py
```

**First real result:** see [`results/FINDINGS.md`](results/FINDINGS.md). Across 5 models,
score-only grading anchored hard on an injected reference — marking correct answers wrong
under a poisoned key. A 2×2 factorial (`--condition A|B|C|D`, verify-instruction ×
explanation) then isolated the fix: the verify *instruction alone was inert*, requiring a
*written worked solution* was the main lever (but incomplete for some models), and
requiring *both* eliminated the measured effect in all five. The dangerous config is the
common one — LLM-judge pipelines that demand a bare number/JSON.

**Before any real run, freeze `PREREGISTRATION.md`** — fixed thresholds, ground-truth
strategy, the mandatory positive control, confound controls (poison plausibility,
paraphrase equivalence, position/verbosity bias, non-determinism), sample size, and
the stop rule. It also pins the claim wording: a flag supports *"model M as a grader
depends on channel X"*, **not** *"benchmark X is unreliable"* (that is the more
confounded, model-specific Path B, not built yet).

Dependency-free (stdlib `urllib` only). No third-party packages, no API traffic
unless a key is set.

## Confirmatory: Contextual Conclusion Capture

The corrected provenance-injection experiment found that a conflicting conclusion can reduce
judge discrimination without a general solver-label premium or an added persuasive-rationale
effect. The frozen 16-item confirmation is specified in
[`PREREG_contextual_conclusion_capture_confirmatory.md`](PREREG_contextual_conclusion_capture_confirmatory.md).
The completed run and fail-closed scorecard are reported in
[`results/FINDINGS_contextual_conclusion_capture_confirmatory.md`](results/FINDINGS_contextual_conclusion_capture_confirmatory.md).
An explicitly post-hoc paired-choice view expresses capture as the probability that the
correct candidate loses at the conflict fork; see
[`results/confirmatory_choice_probability.md`](results/confirmatory_choice_probability.md).

The follow-up causal architecture test is frozen in
[`PREREG_contextual_capture_architecture.md`](PREREG_contextual_capture_architecture.md).
For continuation in a fresh context, start with
[`HANDOFF_contextual_conclusion_capture.md`](HANDOFF_contextual_conclusion_capture.md).
The proposed integrity-first benchmark is specified in
[`BENCHMARK_BLUEPRINT_judge_integrity.md`](BENCHMARK_BLUEPRINT_judge_integrity.md).

Free schedule check (no key and no API calls):

```bash
python3 experiments/run_provenance_injection.py --confirmatory --dry-run
```

The real run is deliberately two-step: prepare and freeze the eight new text sets first, then
run the judge schedule. Confirmatory outputs use separate filenames and cannot overwrite Stage 2.

---

## `swarm_v4/` — does a swarm's cross-checking survive coherent poison?

A provenance-explicit Monte Carlo model, sitting downstream of the CCC result. CCC
found that models accept conclusions embedded in rich context; `swarm_v4/` asks what
happens when a swarm of such models cross-checks against evidence whose *apparent*
diversity overstates its evidential independence — N apparent sources folding onto
M hidden provenance roots.

The headline is a **silent** collapse: as M falls, planner discrimination drops while
commit rate *rises* and latency is unchanged, so no operational metric reports the
attack. A second result sharpens the mechanism — coherent poison does not degrade
cross-checking in general, it disables it selectively on exactly the items that
needed it, leaving aggregate verification metrics looking healthy.

This is a mechanism model producing testable predictions, not an empirical finding
about real swarms; the model is constructed so the aggregation penalty cannot fail to
appear. See [`swarm_v4/walkthrough.md`](swarm_v4/walkthrough.md) for the claims and
[`swarm_v4/README.md`](swarm_v4/README.md) for how to reproduce it.
