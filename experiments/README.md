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
transforms. Wiring a **real judge model** in is the next experiment: implement the
`Judge` protocol sketched at the bottom of the file — `evaluate()` and `verdict()`
stay unchanged; only `evidence_quality` and the channels become real.
