# Benchmark blueprint - integrity-first model evaluation

## Thesis

Build a benchmark in which judge integrity is an explicit, continuously tested property of the
evaluation system. The benchmark should not assume that an LLM judge remains independent after
seeing a reference, another candidate's conclusion or an earlier critique.

The goal is not to claim that contextual capture has been eliminated in every possible form.
The goal is to design the information flow so the known pathway is blocked, disagreements are
routed safely, and residual dependence is measured on every release.

## Core architecture

```text
candidate submission
        |
        +--> deterministic checks (when available)
        |
        +--> isolated candidate assessor
        |       sees: task + rubric + one candidate
        |       never sees: gold conclusion, other candidates, prior critiques
        |
        +--> independent question-only verifier
                commits conclusion before seeing candidate/reference
                          |
                    agreement audit
                     /          \
                 agree        conflict
                   |              |
             ordinary path    quarantine all conclusions
                                  |
                         fresh blind adjudicator
                                  |
                         evidence-based resolution
```

All stages write immutable, hash-addressed evidence. No downstream prompt silently inherits an
upstream conclusion.

## Benchmark layers

### 1. Machine-verifiable core

Start with domains where correctness can be determined independently of an LLM judge:

- executable code and property tests;
- numerical and symbolic problems with code-verified gold;
- structured data transformations with exact schemas;
- constraint satisfaction and planning with executable validators;
- factual tasks backed by frozen, cited source packets and deterministic extraction checks.

This layer anchors the benchmark and measures judge errors against external truth.

### 2. Structured-rubric extension

For genuinely open-ended tasks, decompose quality into claims that can be assessed separately.
Each assessor sees one candidate only and records evidence before assigning scores. Candidate
comparisons happen only after independent assessments are committed.

### 3. Conflict adjudication

Any disagreement among deterministic checks, independent verifiers, candidate assessors or
references triggers a fresh adjudication context. The adjudicator receives the task, rubric,
candidate and relevant source evidence, but not the competing conclusions or their authors.

If the disagreement cannot be resolved without revealing conclusions, reveal them only after
the adjudicator has committed an independent analysis. Record pre- and post-revelation outputs
separately.

## Continuous integrity probes

Every evaluation release includes hidden mirrored sentinels:

- correct versus plausible wrong reference;
- reference present versus quarantined;
- candidate order and presentation swaps;
- source identity swaps with content held fixed;
- bare conclusion versus full rationale;
- irrelevant confident text;
- paraphrased candidates with equivalent content;
- deliberate conflict cases that must activate the router.

These probes are not mixed silently into the model-quality score. They audit the evaluator.

Key metrics:

- `capture_delta = discrimination(clean) - discrimination(wrong_reference)`;
- `correct_branch_probability` using paired candidate scores and half-credit ties;
- `router_recovery = discrimination(router, wrong_reference) - discrimination(contaminated, wrong_reference)`;
- conflict detection sensitivity and false-conflict rate;
- position, identity and wording sensitivity;
- judge calibration against machine-verifiable truth;
- **judge stability**: per-cell repetition SD (k >= 3), published per judge — an unstable
  judge fails the gate regardless of its mean accuracy;
- missingness and retry rates by every experimental factor.

Evaluator-integrity thresholds are frozen before a release. If the evaluator fails, the model
leaderboard is withheld rather than statistically "corrected" after the fact.

## Information-flow rules

1. A judge never sees the gold answer before committing its own analysis.
2. A judge never sees another candidate's conclusion while scoring a candidate.
3. References are data for a router or post-commit audit, not ordinary judge context.
4. Solver, assessor, router and adjudicator calls use fresh contexts.
5. Prompt hashes, model identifiers, provider routes, temperatures, token limits, retries and
   parsing failures are published.
6. At most one successful observation exists per intended cell; retries remain evidence.
7. Missingness is never interpreted as model safety.
8. Deterministic validators outrank model consensus when their scope is valid.

## Scoring and publication

Publish three separate outputs:

1. **Task performance** - model quality on benchmark tasks.
2. **Evaluator integrity** - contextual capture, invariance, calibration and routing metrics.
3. **Coverage and cost** - missingness, escalation frequency, latency and API/token cost.

Do not collapse these into one opaque number. A task score is publishable only when the
evaluator-integrity gate passes. Report confidence intervals clustered over task families, not
individual repeated calls.

### Uncertainty is a first-class output

A leaderboard that prints `71.3` vs `70.8` with no interval is claiming a distinction it never
measured. Every published score carries an uncertainty estimate, and the variance is reported
**decomposed**, because a single pooled standard deviation conflates sources with different
meanings:

1. **Item variance** (which questions were asked). The dominant component. Reported as an
   item-clustered bootstrap interval — not a plain SD, because scores saturate at the scale
   ends and repetitions within an item are correlated, so an SD would look precise while
   being wrong.
2. **Repetition variance** (judge stability). The same cell run k >= 3 times measures the
   judge's run-to-run instability, even at temperature 0. This is a property of the
   *evaluator*, published per judge as a reliability statistic. A judge that scores the same
   item [100, 0, 100] across reps is not a usable instrument, and a single-pass benchmark
   cannot detect this at all — the intermittent poison failures in the sensitivity autopsy
   (rep patterns like [1.0, 0.0, 1.0]) were invisible to any one pass.
3. **Wording variance** (prompt sensitivity). Measured by the mirrored paraphrase probes;
   published as the between-variant spread against the within-variant noise floor. This
   component can exceed the model differences being ranked and is almost never measured.

Condition/model variance is the effect under study and stays out of the error bar.

**Ranking rule:** two models whose intervals overlap are reported as *statistically
indistinguishable at this benchmark's resolution* — the leaderboard shows the tie rather than
an unearned ordering. Ranks are claims; intervals are the evidence for them.

Repetitions are what make any of this measurable: a benchmark that evaluates each item once
has no repetition variance to report and no way to detect an unstable judge. k >= 3 is the
floor, priced into the cost budget from the start.

## Dataset governance

- Keep public development tasks separate from rotating private evaluation tasks.
- Generate task families from executable specifications where possible.
- Hash and version every task, rubric, validator and prompt template.
- Use canary strings and periodic replacement to detect leakage or memorization.
- Maintain a signed release manifest and immutable raw evidence bundle.
- Pre-register changes before viewing new model outcomes.
- Preserve failed and superseded runs with explicit exclusion reasons.

## MVP

### Phase A - integrity laboratory

- Reuse the current 16-item numerical set.
- Implement the four frozen architectures now being tested.
- Establish capture, recovery, routing and cost metrics.
- Add synthetic judges that must pass/fail known controls.

### Phase B - benchmark v0.1

- Expand to at least 100 executable task instances across five task families.
- Hold out generators and seeds from development.
- Run at least three independent judge families.
- Require the evaluator-integrity gate before publishing rankings.

### Phase C - open-ended extension

- Add source-grounded writing, analysis and planning tasks.
- Use claim-level rubrics and blind evidence packets.
- Escalate unresolved conflicts to a fresh panel or human review.

### Phase D - external adapters

- Reproduce public evaluation pipelines for selected existing benchmarks.
- Apply mirrored reference and isolation probes without changing candidate outputs.
- Name a benchmark only when its actual published pipeline is reproduced; otherwise label the
  result as a reconstruction.

## Immediate decision after the active run

Use the architecture experiment to choose the default v0.1 evaluator:

- If context isolation recovers discrimination and the router adds little, prefer the simpler
  isolated architecture.
- If the router provides material recovery or cost savings, use isolation as the default and
  routing as the escalation layer.
- If both remain vulnerable, do not launch an LLM-judged leaderboard; expand deterministic
  validation and redesign adjudication first.

