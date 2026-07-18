# Contextual Conclusion Capture: LLM Judges Defer to Conflicting Conclusions Across Reasoning Domains, and Only Context Isolation Reliably Prevents It

**Author:** Pete Sherratt · *affiliation and contact to be completed before submission*

**Preprint draft — 2026-07.** All numeric results in this paper are produced by preregistered,
publicly committed experiments with streamed evidence and independent re-analysis; see the
Reproducibility appendix for the exact artifacts, hashes, and per-result findings files.

---

## Abstract

Large language models are increasingly used to *judge* the outputs of other models, often by
comparing a candidate answer against a reference. We identify and characterise a failure mode we
call **Contextual Conclusion Capture (CCC)**: an LLM judge's ability to distinguish correct from
incorrect candidates deteriorates when a *conflicting conclusion* is present in its evaluation
context — independent of that conclusion's stated authority or supporting rationale. Through a
sequence of preregistered experiments across five model endpoints, we falsify two intuitive
explanations (deference to an authoritative source; persuasion by an elaborate argument) and show
that a **bare, neutrally-labelled wrong answer is sufficient** to induce capture. We then test
whether the failure survives a change of reasoning domain, using three domains that all admit
**mechanical, non-circular gold**: arithmetic word problems, Python function implementations
(unit-test gold), and relational SQL queries (SQLite oracle). CCC replicates in all three, but
its magnitude and even *which models are vulnerable* are **domain-dependent**: a judge that is not
significantly captured in the code domain is the *most* captured in the SQL domain, where capture
is universal across all five models and severe enough to *reverse* the judge's ordering (it scores
the wrong answer above the correct one). We evaluate three mitigations under mirrored
correct/wrong-reference sentinels. Prompt-level written verification reduces but never eliminates
capture in any domain; a mechanical conflict-router recovers discrimination where the underlying
comparison is clean; and **context isolation** — never placing the foreign conclusion in the
judge's context — is the only safeguard with a *structural, byte-audited* guarantee that holds in
every domain tested. We argue that these results imply evaluator integrity must be treated as a
**per-release, per-domain gate** rather than a property established once, and we release all items,
harnesses, preregistrations, and evidence.

---

## 1. Introduction

"LLM-as-a-judge" has become a default tool for evaluating open-ended model behaviour, powering
leaderboards, preference data pipelines, and automatic regression tests. A judge is typically shown
a task, a candidate answer, and sometimes a reference answer, and asked to score or compare. This
convenience rests on an unstated assumption: that the judge grounds its verdict in the *evidence*
(the task and the candidate), not in whatever other conclusions happen to share its context.

We show that assumption fails in a specific, reproducible way. When a conflicting conclusion — for
example, a plausible but wrong "reference" answer — is placed in the judge's context, the judge
often stops grading the candidate on its merits and instead grades it by *agreement with the
conflicting conclusion*. We call this **Contextual Conclusion Capture (CCC)**.

The contribution of this paper is threefold:

1. **Mechanism.** We isolate the active ingredient. It is not that the foreign conclusion carries
   authority (a "solver" or "reference" label adds nothing), and not that it is persuasively
   argued (a bare wrong number does as much damage as a full wrong derivation). The presence of a
   *competing conclusion* is itself sufficient (§4–§5).
2. **Generality with heterogeneity.** We replicate CCC across three reasoning domains that keep
   gold mechanical and non-circular — arithmetic, imperative code, and relational SQL — and find
   that both the size of the effect and *which models are affected* change substantially with the
   domain (§6). Robustness does not transfer: certifying a judge in one domain says little about
   another.
3. **What actually prevents it.** Under mirrored sentinels we compare three mitigations and find a
   clear ordering that holds across domains: **context isolation ≥ conflict routing ≫ written
   verification.** Only isolation offers a structural guarantee — we verify, byte-for-byte, that
   the foreign conclusion never enters the judge's prompt — rather than a behavioural one (§7).

Every experiment was preregistered before data collection, uses fail-closed handling of missing
observations, streams auditable evidence, and was re-analysed independently from the raw scores.
We regard this methodological discipline as part of the contribution: measuring a judge's integrity
is itself a judgement problem, and the study is designed so that no model is ever asked to
establish the ground truth it is being evaluated against.

---

## 2. Related work

**LLM-as-a-judge and its biases.** Using strong LLMs as evaluators was popularised by MT-Bench and
Chatbot Arena (Zheng et al., 2023) and reference-based variants such as G-Eval (Liu et al., 2023).
A growing literature documents systematic biases: position/order bias and the observation that LLM
evaluators are "not fair evaluators" (Wang et al., 2023); verbosity and self-preference, where
evaluators favour longer answers or their own generations (Panickssery et al., 2024). CCC is
related but distinct: it is not a preference over surface features of the *candidate*, but a
deterioration of *discrimination* caused by a conflicting conclusion elsewhere in context, and we
show it is separable from authority and from argument quality.

**Sycophancy and anchoring.** LLMs tend to agree with assertions in their context and to defer to
stated user beliefs or "expert" claims (Sharma et al., 2023, on sycophancy). CCC can be read as an
evaluation-time anchoring effect, but our controls show the anchor need not be authoritative or
argued — a neutral, unsupported wrong answer suffices — which rules out a pure authority-deference
account.

**Prompt injection and context contamination.** Indirect prompt injection studies how untrusted
content in context subverts a model's behaviour (Greshake et al., 2023). CCC is a benign-context
analogue: the "injection" is simply a wrong reference answer of the kind an ordinary evaluation
pipeline pastes into the judge prompt, and the harm is silent mis-scoring rather than hijacked
instructions.

**Reasoning and verification.** Chain-of-thought (Wei et al., 2022) and self-consistency (Wang et
al., 2022) improve task accuracy by eliciting or aggregating reasoning. A natural hypothesis is
that asking the judge to reason/verify first would cure CCC. We test this directly and find it
reduces but does not eliminate the effect in any domain — motivating an architectural rather than a
prompt-level fix.

*Bibliographic details above should be verified against primary sources before submission.*

---

## 3. Contextual Conclusion Capture, defined

Let a judge assign a score \(s\in[0,100]\) to a candidate answer for a task. For a task with a
known-correct candidate and a matched known-wrong candidate, define **discrimination**

\[
D \;=\; \operatorname{mean}\,s(\text{correct}) \;-\; \operatorname{mean}\,s(\text{wrong}).
\]

A grounded judge has \(D>0\): it scores correct answers above wrong ones. We introduce a
**conflicting conclusion** into the judge's context — a claim, presented as a neutral reference
note, that the answer is the *wrong* value — and measure the drop in discrimination,

\[
\text{harm} \;=\; D_{\text{no injection}} \;-\; D_{\text{injection}}.
\]

> **Contextual Conclusion Capture** is the phenomenon of \(\text{harm}>0\): the mere presence of a
> conflicting conclusion in the evaluation context degrades a judge's ability to distinguish
> correct from incorrect candidates, *independent of the conclusion's stated authority or
> supporting rationale.* When harm exceeds \(D_{\text{no injection}}\), discrimination becomes
> negative — the judge **reverses**, scoring the wrong candidate above the correct one.

Two mirror conditions let us make the effect causal rather than correlational. In the *mirrored
reference* design, the same item is judged once with a *correct* reference and once with a *wrong*
reference; the difference in discrimination, **susceptibility** \(=D_{\text{correct ref}} -
D_{\text{wrong ref}}\), isolates the effect of flipping only the reference.

---

## 4. Method

**Models.** Five hosted endpoints spanning four providers, accessed through a common API:
`openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`, `google/gemini-2.5-flash`,
`deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct`. These are cost-efficient models; the
claims concern the *existence and structure* of the failure, not a ranking of frontier systems (see
Limitations).

**Protocols.** Each judging cell uses one of two protocols: `score_only` (return only a JSON score)
and `verify_written` (independently work out the answer in writing, then score). The latter tests
the "reason/verify first" mitigation.

**Conditions.** The conflicting conclusion is factored into *content* × *label*: `no_injection`;
`neutral / answer_only` (a bare wrong result, no argument — the **primary** condition);
`neutral / full_wrong_rationale` (the wrong result with a fabricated justification); and
`solver / full_wrong_rationale` (the same, attributed to an authoritative source). Comparing these
separates provenance (label) and rationale (argument) from the bare conclusion.

**Mechanical, non-circular gold.** Correctness is never decided by a model. In every domain the
correct and wrong candidates are produced by an executable oracle (arithmetic computed in code;
Python graded by a frozen unit-test suite in a sandbox; SQL results from SQLite), so the labels the
judge is measured against are ground truth by construction. This is essential: measuring a judge's
integrity with another judge would be circular. It also bounds the study to domains where such gold
exists — a deliberate scope, not an oversight (§8).

**Preregistration and integrity.** For each confirmatory run we froze, before any API call: the
items and a hash of them, the conditions, the primary and secondary contrasts, the decision rule,
the repetition count and schedule seed, the model set, and the missingness policy. Support requires
a 95% item-clustered bootstrap confidence interval excluding zero in the predicted direction and a
completeness floor (≥75% of items). Analysis is **fail-closed**: an item enters a contrast only if
all required repetitions of every required cell succeeded; missingness is reported *before* any
estimate and never interpreted as safety. Evidence is streamed to append-only JSONL with a
hash-keyed prompt manifest; the deduplication key is the frozen cell identity, and at most one
successful observation per cell is permitted. Every headline number was recomputed independently
from the raw scores. In the mechanically-gradable domains the run additionally recomputes a
**gold-signature** at start and aborts if the local oracle would produce different results —
converting, e.g., an unexpected SQLite version into a refusal to run rather than silent corruption.

---

## 5. Establishing the phenomenon and its mechanism (arithmetic)

**The phenomenon and the fragility of prompt fixes.** In a 16-item arithmetic pilot, injecting a
poisoned reference answer collapsed discrimination for every model under score-only judging. A 2×2
factorial separating a *verify instruction* from a *requirement to show written work* found the
instruction alone inert, written work the main lever but incomplete for some models, and only the
combination driving the measured gap to zero — an interaction, not a main effect. A preregistered
wording-sensitivity matrix then showed the prompt-level fix is model-specific and phrasing-fragile:
one model regressed on the most rigid, "structural-looking" template. An audit of failing
transcripts found the judge computing the correct answer in its own working and then scoring the
correct candidate zero — in one case asserting "8 does not match my calculation of 8." The verdict
was controlled by the reference, not by the demonstrably-correct computation the model had just
written. This is the core motivation: **visible reasoning does not reveal what controlled the
verdict.**

**Falsifying authority and persuasion.** A provenance × content factorial, confirmed in a separate
preregistered run, isolates the active ingredient. Naming the source ("Solver") added no capture
over a neutral label in any model, and for one model *reduced* it. A full wrong rationale did not
capture more than a bare wrong answer; the bare answer was as effective, sometimes more. The
sub-hypotheses that CCC is authority-deference, or persuasion by argument, are therefore falsified.
What remains is the conflicting conclusion itself.

**Can architecture prevent it?** A causal architecture experiment (16 items, mirrored
correct/wrong references) compared four pipelines: a contaminated score-only judge; a contaminated
verify-written judge; a **context-isolated** judge that never receives the reference; and a
**conflict-router** that independently re-solves the task, compares its own conclusion to the
reference mechanically, and quarantines the reference on disagreement. Context isolation was the
most consistent safeguard and passed a byte-level audit — every isolated judge prompt was
hash-identical whether the reference was correct or wrong, so the reference provably could not act.
The router helped some models but not all; written verification attenuated but did not abolish
capture. Full numbers: [`experiments/results/FINDINGS_contextual_conclusion_capture_confirmatory.md`],
[`.../FINDINGS_contextual_capture_architecture.md`].

---

## 6. Domain generalization: does CCC survive a change of reasoning?

Both prior domains are, at bottom, "compute a deterministic result." To test whether CCC is an
artifact of that task shape, we replicated the full two-stage design (a Stage-1 injection test and a
Stage-2 architecture test, conditional on Stage-1 capture) in two further domains chosen to keep
gold mechanical while changing the reasoning substrate.

### 6.1 Code (imperative program semantics)

The judge scores a Python implementation against a specification; gold is a frozen unit-test suite
executed in a deterministic sandbox. The bare-conclusion primary was **supported in 4 of 5 models**
(+36 to +44 discrimination points); DeepSeek's interval included zero by 0.21 points and, per the
frozen rule, was called *not supported* — no rounding. A notable side result: Claude Haiku, which in
arithmetic refused the bare-score format 42% of the time and was therefore unmeasurable, complied
perfectly in code (0/384 failures) and, once measurable, was captured (+40) — its earlier
non-compliance was format-specific, not protective. In Stage 2, context isolation and the router
were each supported for 3 of 4 measurable models (isolation byte-audited, 384/384 identical prompt
pairs); written verification was supported for **no** model.
[`experiments/results/FINDINGS_ccc_codedomain.md`]

### 6.2 Relational (declarative SQL)

The judge scores a claimed query result against a frozen SQLite fixture; gold is the SQLite oracle,
protected by the fail-closed gold-signature gate (which confirmed byte-identical gold when the run
machine's SQLite 3.50.4 differed from the 3.45.1 of development). This is the **strongest and most
uniform** capture of the three domains. The bare-conclusion primary was supported in **all five
models at +106 to +153 points** — roughly twice the code magnitude. A per-arm decomposition shows a
genuine *reversal*: with no injection the judge scores correct high and wrong low; with the bare
wrong-result note, correct collapses toward 0 and wrong rises toward the injected value, so
discrimination goes negative. The same judges discriminate correctly when not injected, ruling out a
saturation artifact.

| Model | baseline \(D\) | injected \(D\) | correct: base→inj | wrong: base→inj |
|---|---:|---:|---:|---:|
| gpt-4o-mini | +31.6 | −80.6 | 79.9 → 0.0 | 48.3 → 80.6 |
| claude-haiku-4.5 | +54.2 | −58.3 | 79.2 → 4.2 | 25.0 → 62.5 |
| gemini-2.5-flash | +41.2 | −83.3 | 63.5 → 0.0 | 22.3 → 83.3 |
| deepseek-chat | +67.8 | −85.4 | 92.1 → 2.1 | 24.2 → 87.5 |
| llama-3.3-70b | +41.4 | −66.7 | 80.6 → 0.0 | 37.3 → 66.7 |

All five models entered Stage 2. Isolation restored discrimination to *reference-neutrality* for
every model — under isolation the correct-vs-wrong-reference gap is ≈ 0 (Claude exactly 0.00),
and because the prompt pairs are byte-identical (720/720) the reference provably cannot act. The
router fully recovered discrimination for all five (its strongest showing, since comparing a
canonical query result is exactly what a mechanical comparator does best). Written verification's
mitigation *delta* is large, but the honest measure — residual capture still present under
verification — remains supported for 4 of 5 models (small for GPT and Claude, ≈0 only for Gemini,
but +50.9 for DeepSeek and +56.2 for Llama). [`experiments/results/FINDINGS_ccc_sql.md`]

### 6.3 Cross-domain synthesis

| | Arithmetic | Code | SQL |
|---|---|---|---|
| Primary capture (score-only) | supported (4/4 measurable) | supported 4/5 | **supported 5/5** |
| Magnitude (points) | +39 to +88 | +12 to +44 | **+106 to +153** |
| Isolation (byte-audited) | most consistent | 3/4 | **5/5, restores neutrality** |
| Conflict router | partial (some models) | 3/4 | **5/5 (full recovery)** |
| Written verification | partial | supported for none | partial (residual 4/5) |

Two findings cut across the table. First, **capture is model- and domain-dependent, decisively**:
DeepSeek is *not* significantly captured in code (+10.2, CI includes 0) yet is *the most* captured
in SQL (+153). A judge's robustness does not transfer across domains. Second, **safeguard efficacy
is also domain-dependent, with one invariant**: written verification is partial everywhere and never
a complete fix; the router recovers where the underlying mechanical comparison is clean (partial in
code, total in SQL); and **only context isolation carries a structural, byte-level guarantee that
holds in every domain** — its neutrality is a property of construction, not of model behaviour.

We note, but do not claim, a pattern consistent with the data: capture magnitude appears to track
*verification difficulty* (relational answers, requiring mental execution of joins/GROUP BY/NULL
logic, are harder to independently check than arithmetic, and show both lower baseline
discrimination and larger capture). This is a hypothesis for future work, not a tested result.

---

## 7. Implications for evaluation design

The results argue against two common practices and for a specific architecture.

- **Do not paste a reference answer into the judge's context and hope a prompt keeps it honest.**
  Reference-anchoring is real, prompt-level verification is incomplete in every domain we tested, and
  its efficacy is model- and wording-specific.
- **Do not certify a judge once.** Because capture and safeguard efficacy are domain-dependent, an
  evaluator validated on one task family carries no guarantee on another. Integrity must be a
  **per-release, per-domain** property, tested with mirrored correct/wrong-reference sentinels that
  run in the same conditions as the real items.
- **Prefer structural separation to behavioural instruction.** Keep the foreign conclusion out of
  the first-pass judge context; evaluate candidate and reference independently; compare their
  conclusions mechanically; expose conflict rather than allowing silent reconciliation; and route
  disagreement to another source of verification (a deterministic checker, an independent solve, or
  a human). Isolation is the only mitigation whose guarantee we can audit at the byte level; the
  router is a strong complement where a mechanical comparison of conclusions is available.

A companion design sketch treats these properties as an evaluation *release gate* — machine
verification where possible, reference quarantine, fresh conflict adjudication, mirrored sentinels,
and separate reporting of task performance, evaluator integrity, and uncertainty — rather than as
hidden assumptions.

---

## 8. Limitations

- **Small, hand-authored micro-domains.** Each domain uses 16–24 frozen items. The study establishes
  the *existence, mechanism, and structure* of CCC and the relative ordering of mitigations; it is
  not a benchmark of any deployed system.
- **No named-benchmark or production claim.** We do not test MT-Bench, AlpacaEval, Spider, or any
  production evaluator. Such a claim would require reproducing that system's actual judge prompt,
  reference visibility, ordering, routing, retry, and aggregation.
- **Cost-tier models.** All five endpoints are small/efficient models. Whether frontier judges are
  equally susceptible is untested; the model-dependence we observe makes this an important open
  question rather than a safe extrapolation.
- **Coarse scores.** Judges frequently saturate at 0/100; the key results (the reversal, isolation
  neutrality) are established by decomposition and by preregistered support calls, not by treating
  point magnitudes as precise.
- **Mechanical-gold domains only.** Open-ended judging — where the Stage-2 comparison would itself
  become a judgement — is deliberately out of scope, because rigor there would reintroduce the
  evaluator-for-the-evaluator circularity this method avoids. A deterministic test-oracle router
  (using the unit tests or the SQLite oracle directly as the conflict signal) is specified but
  untested.
- **Confidence intervals over ≤24 items** are wide; we report item-clustered bootstrap intervals and
  treat overlapping intervals as a conservative tie, not a significance test.

---

## 9. Conclusion

LLM judges can be captured by a conflicting conclusion placed in their context, and the conclusion
needs neither authority nor argument to do it — its mere presence is enough. The failure is real,
preregistration-robust, and it generalises across three computational-reasoning domains, but its
magnitude and its victims shift from domain to domain: robustness earned in one setting does not
carry to another. Among the mitigations we tested, prompt-level verification is never sufficient and
a mechanical router helps only where conclusions can be compared cleanly; the single intervention
that reliably works, and whose guarantee we can verify byte-for-byte, is the simplest — do not let
the foreign conclusion into the judge's context. Evaluator integrity is not a property to assume; it
is a property to gate on, every release and every domain.

---

## Reproducibility appendix

All code, items, preregistrations, streamed evidence, and per-experiment findings are in the project
repository. Key artifacts:

- **Narrative and index of all twelve experiments:** `RESEARCH_NARRATIVE.md`.
- **Preregistrations (frozen before data):** `experiments/PREREG_*.md` (arithmetic confirmatory and
  architecture; code domain; SQL domain), each with item hashes, seeds, contrasts, thresholds, and
  missingness policy.
- **Frozen items + oracles:** `experiments/ccc_code_items.py` + `ccc_code_runner.py` (sandboxed
  unit-test grader); `experiments/ccc_sql_items.py` (SQLite fixtures, queries, canonicalizer, and
  gold signature). Both self-verify and are hash-pinned; gold was checked byte-identical across
  CPython 3.10–3.13, and (SQL) across SQLite versions via the run-time gold-signature gate.
- **Run adapters:** `experiments/run_ccc_codedomain*.py`, `experiments/run_ccc_sql*.py`. The SQL
  adapters use a fixed concurrent worker pool with a single writer; all concurrency invariants
  (frozen schedule/cell identity independent of completion order, one flushed writer, dedup by cell
  identity, resume retrying only non-successful cells, failures preserved as fail-closed missingness)
  were verified offline and re-checked on the live evidence.
- **Unified per-domain findings:** `experiments/results/FINDINGS_ccc_codedomain.md`,
  `.../FINDINGS_ccc_sql.md`; plus stage records and the offline audit log
  `.../ccc_code_offline_audit.txt`.
- **Evidence:** streamed `*_obs_*.jsonl` (one row per judge attempt), `*_prompts_*.jsonl` (prompt
  manifest), `*_solver_*.jsonl` (router solves), and `*_meta_*.json` (seeds, hashes, oracle versions,
  worker count) for each stage. Every reported estimate is auditable back to a stored transcript.

**Integrity summary.** Across the six domain-stage runs analysed here: one row per intended cell,
maximum one attempt per cell, zero duplicate successful cells, zero order-index/cell mismatches
under concurrency, all prompts resolvable in the manifests, factor-correlated missingness disclosed
and fail-closed, and all headline contrasts recomputed independently from the raw scores.

*Acknowledgement: experiments were implemented and analysed with AI-assisted tooling; all
preregistrations, decision rules, and interpretations were fixed by the author.*
