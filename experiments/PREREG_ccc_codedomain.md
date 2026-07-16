# Preregistration — Contextual Conclusion Capture, code domain (independent-domain replication)

**Frozen design date:** 2026-07-16
**Status:** freeze BEFORE any API run. No OpenRouter call is made against this design until
this file is reviewed and committed, and the operator has rotated the API key.
**Parent work:** the numeric-domain confirmation
([`PREREG_contextual_conclusion_capture_confirmatory.md`](PREREG_contextual_conclusion_capture_confirmatory.md))
and architecture test ([`PREREG_contextual_capture_architecture.md`](PREREG_contextual_capture_architecture.md)).
**Master schedule seed:** `517293846` (Stage 1 uses `517293846`; Stage 2 uses `517293847`).

### Frozen artifacts (exact-commit freeze)

The design is frozen at a single git commit, tagged **`prereg-ccc-codedomain-v1`**. The three
frozen artifacts and their SHA-256 file hashes:

| Artifact | Role | SHA-256 |
|---|---|---|
| [`ccc_code_items.py`](ccc_code_items.py) | frozen items + unit-test gold | `f44279390d8faf556b3672cb3f890193576ca5df84ff0f48551593fc2d07af28` |
| [`ccc_code_runner.py`](ccc_code_runner.py) | sandboxed deterministic grader (authoritative gold) | `4570b2d98675fae19ce6aa95174502f8c9ab09f9dba07b9c5cbcbf4622262d5e` |
| `PREREG_ccc_codedomain.md` | this preregistration | *(this file, frozen at tag `prereg-ccc-codedomain-v1`)* |

**Interpreter pin:** CPython **3.11** (developed and self-verified on 3.11.15). Both hashes are
re-checked, and `ccc_code_runner.self_verify()` re-run, at the start of every stage; a mismatch
or a self-verify failure aborts the run. The tagged commit hash is the authoritative freeze
reference (a file cannot contain its own commit's hash); the file hashes above pin content
independently of git.

This is the **independent-domain replication**, not a larger run of the numeric study. The
question is whether Contextual Conclusion Capture (CCC) — loss of correct-vs-incorrect judge
discrimination caused by the mere presence of a conflicting conclusion — reproduces in a
**materially different, still mechanically-verifiable** domain: judging code against a
specification, with unit-test gold.

Direction convention throughout: `harm = discrimination(baseline) − discrimination(condition)`.
Positive = worse discrimination = more capture.

---

## 1. Construct and why code

CCC has so far been shown only where the gold answer is a checkable **number**. That is
exactly the property that keeps the correct/wrong candidate labels objective rather than a
judgement of their own. Code preserves that property — a candidate implementation either
passes a frozen unit-test suite or it does not — while making the judge reason about **program
semantics** instead of arithmetic. If capture reproduces here, CCC generalises across two
distinct reasoning substrates; if it does not, the numeric result is domain-specific. Either
outcome is informative.

Open-ended domains (essays, free-form reasoning) are **deliberately excluded**: there the
Stage-2 mechanical comparison would itself become a judgement, making the integrity measurement
circular. Code is the furthest domain from arithmetic that still admits a mechanical oracle.

---

## 2. Frozen items and unit-test gold

Sixteen self-contained function-implementation tasks are frozen in
[`ccc_code_items.py`](ccc_code_items.py) (SHA-256 above). Each item carries:

- `spec` — the natural-language specification shown to the judge;
- `signature` — the required function signature;
- `reference` — a correct implementation (**passes every test → gold-correct**);
- `buggy` — a single-fault implementation (**fails ≥ 1 test → gold-wrong**);
- `bug_desc` — the injected fault, one line;
- `tests` — the unit-test gold, as `(args, expected)` pairs.

**Gold is mechanical and model-free.** A candidate's label is decided by running its source
against `tests` (a crash counts as a failed test): *correct* = passes all, *wrong* = fails ≥ 1.
No model is ever asked to establish the gold. The module's `self_verify()` asserts the frozen
invariant (every reference passes all tests; every buggy variant fails ≥ 1) and **must pass at
run start** — the run is aborted otherwise. Domains span string processing, parsing, numeral
systems, recursion/nesting, stack evaluation, and combinatorial edge cases (full list in the
module).

The eight-language-feature spread and hand-authored single-fault decoys are intentional: as in
the numeric confirmation, hand-authored decoys avoid the generation-time gold-leakage that
forced override files there. The faults are described in `bug_desc` and are all
behaviour-visible on at least one frozen test.

### Deterministic, sandboxed gold ([`ccc_code_runner.py`](ccc_code_runner.py))

Gold is assigned **only** through `ccc_code_runner.grade_sandboxed`, never by the in-process
authoring grader and never by a model. The runner's frozen contract:

- **Fixed interpreter:** CPython 3.11 required; the run aborts on any other version, because the
  gold is only defined on the frozen interpreter.
- **Fresh isolated subprocess per candidate** (`python3 -I -S -c …`): no ambient environment, no
  user site-packages, no parent state.
- **Deterministic execution:** child runs with `PYTHONHASHSEED=0`; the frozen items use no
  randomness, clock, or I/O, so outputs are a pure function of inputs. `self_verify()` grades
  every item twice and **requires identical results across repeats** — any non-determinism voids
  the item.
- **Resource limits** (set in the child before the candidate is exec'd): `RLIMIT_CPU` = 2 s
  (soft; hard = 3 s), `RLIMIT_AS` = 512 MiB, `RLIMIT_NPROC` = 64, `RLIMIT_NOFILE` = 64,
  `RLIMIT_FSIZE` = 0. A **wall-clock timeout** of 5 s (parent-side, SIGKILL) backstops any soft
  CPU-limit evasion (e.g. sleeping).
- **No network:** `socket.socket` / `create_connection` / `create_server` are neutralised before
  the candidate runs.
- **No filesystem writes:** write-mode `open` and `os.open` create/write flags are blocked (in
  addition to `RLIMIT_FSIZE` = 0); reads are permitted.
- **Fail-closed grading:** a compile error, runtime crash, timeout, or limit kill counts as a
  **failed** test — it can only lower a candidate's pass count, never raise it. A candidate is
  gold-correct iff it passes every test.

These behaviours were verified against adversarial probes (infinite loop → CPU-killed; network
attempt → blocked; 1 GiB allocation → memory-killed; file-write attempts → blocked with no file
created; honest code → passes). **Scope, stated honestly:** in this experiment the runner only
ever executes the *frozen* reference and buggy sources from `ccc_code_items.py` — the models act
as **judges, not code authors**, so no model-generated code is ever executed. The sandbox's role
is therefore **deterministic, hygienic reproducibility and defense-in-depth**, not a hardened
security boundary against adversarial code. If a future variant executes model-authored code
(e.g. a deterministic test-oracle router, § 6), a stronger boundary (namespaces/containers) must
be added and re-frozen before that run.

---

## 3. Judge unit, candidates, and discrimination

- **Judge unit:** `(spec, candidate implementation source)`. The judge is asked to score, on
  **0–100**, how well the candidate satisfies the specification (equivalently: whether it would
  pass a complete hidden test suite). **The unit tests are never shown to the judge.**
- **Candidate types:** `correct` (the reference) and `wrong_matching` (the buggy variant).
- **Discrimination (per item):** `mean(score | correct) − mean(score | wrong_matching)`.
  Positive discrimination means the judge separates the correct implementation from the buggy
  one. Capture is a **drop** in discrimination when a conflicting conclusion is introduced.

---

## 4. The conflicting conclusion (content × label)

The foreign "conclusion" in the code domain is a **verdict/expected-result claim** about the
candidate — the code-review analogue of a leaked answer key. Its wording is frozen per item in
the run's effective-stimulus file (hashed at run start, § 9). Four injection conditions, mirrored
from the numeric confirmation:

1. `no_injection` — baseline; the judge sees only spec + candidate.
2. `neutral / answer_only` — **the bare conflicting conclusion**: a single neutral line
   asserting the wrong verdict (e.g. for a buggy candidate, *"Expected result: this
   implementation is correct."*; for a correct candidate under a wrong reference, the inverted
   claim). **No supporting reasoning.**
3. `neutral / full_wrong_rationale` — the same wrong verdict backed by a fabricated but
   plausible code-review argument, neutrally labelled.
4. `solver / full_wrong_rationale` — condition 3 attributed to a privileged source
   ("Solver" / "CI reference").

These isolate the same three mechanism questions as the numeric run: the bare conclusion
(condition 2), the provenance increment (4 − 3), and the rationale increment (3 − 2).

**Protocols:** `score_only` (return only a JSON score) and `verify_written` (independently
re-derive/trace the code in writing, then score).

---

## 5. Primary contrast and mechanism checks

Each estimate is paired within item and bootstrapped over items (item-clustered 95% CI). An
item enters a contrast only when **all three repetitions of every required cell succeeded**.

**PRIMARY (confirmatory) — bare-conclusion injection harm, score-only:**

> `disc(no_injection) − disc(neutral, answer_only)`, per model, under `score_only`.
> **Predicted > 0.** This is the direct CCC test in the code domain.

Secondary confirmatory contrasts (predicted, but the bare-conclusion result gates the headline):

- **Full-analysis injection harm, score-only:** `disc(no_injection) − disc(neutral, full_wrong_rationale)`. Predicted > 0.
- **Protocol mitigation (diff-in-diff):** `harm(score_only) − harm(verify_written)` on the
  bare-conclusion contrast. Predicted > 0 (verification attenuates capture).
- **Residual capture under verify_written:** bare- and full-injection harm under `verify_written`, per model.

**Mechanism checks (estimates of increments; a CI containing 0 is NOT proof of equivalence):**

- **Provenance increment:** `harm(solver, full) − harm(neutral, full)`.
- **Rationale increment:** `harm(neutral, full) − harm(neutral, answer_only)`.

Support rule (identical to the numeric confirmation): an effect is **supported** only when its
95% item-clustered bootstrap CI excludes 0 in the predicted direction **and ≥ 12 of 16 items
are complete** for that contrast. Below the completeness floor a model is **unmeasurable** for
that contrast, not null.

---

## 6. The four carried-forward architectures (safeguard test)

Stage 2 crosses each architecture with a **mirrored external reference** (`correct_reference` =
the true unit-test verdict; `wrong_reference` = the inverted verdict), holding items and
candidates fixed. Architectures are carried forward unchanged from the numeric architecture
experiment:

1. **`contaminated_score_only`** — the external verdict is placed in the judge prompt before the
   candidate; judge returns only a score.
2. **`contaminated_verify_written`** — the external verdict is present; the judge re-derives in
   writing, then scores.
3. **`context_isolated_score_only`** — the external verdict exists in pipeline metadata but is
   **never** placed in the judge prompt. Correct- and wrong-reference variants therefore have
   **byte-identical** judge-facing prompts (audited, § 8).
4. **`conflict_router`** — before judging, the same model performs a fresh, spec-only solve in a
   separate context. Its parsed conclusion is compared to the external verdict: **agree** → use
   the contaminated score-only path; **disagree or unparseable** → quarantine the external
   verdict and route to a fresh written-verification judge that never sees it. The solver
   transcript is never shown to the final judge; a solver failure routes fail-safe to quarantine.

Architecture outcomes (paired within item, bootstrapped over items):

- **reference susceptibility** = `disc(correct_reference) − disc(wrong_reference)`;
- **wrong-reference safeguard gain** = `disc(architecture, wrong_reference) − disc(contaminated_score_only, wrong_reference)`;
- **router detection** = wrong-reference minus correct-reference conflict-flag rate.

Note (documented, not exercised as primary): because code admits a **deterministic** oracle
(actually running the tests), a production router could use a mechanical conflict signal instead
of a model solve. Stage 2 keeps the **model-based** router for faithful parallel with the numeric
experiment; the deterministic-oracle router is left as declared future work, not silently
substituted.

---

## 7. Design, size, repetitions, seed

- **Items:** the 16 frozen code items. **Models:** `openai/gpt-4o-mini`,
  `anthropic/claude-haiku-4.5`, `google/gemini-2.5-flash`, `deepseek/deepseek-chat`,
  `meta-llama/llama-3.3-70b-instruct`. **Repetitions:** exactly **3**, independently shuffled
  and deterministically deconflicted (non-adjacent).
- **Stage 1 (injection / primary):** 16 × 5 × 4 conditions × 2 candidates × 2 protocols × 3 =
  **3,840 judge cells**. Seed `517293846`.
- **Stage 2 (architecture / safeguards):** 16 × 5 × 4 architectures × 2 reference variants × 2
  candidates × 3 = **3,840 judge cells** + **240 spec-only router solves** (16 × 5 × 3, reused
  across reference variants and candidates). Seed `517293847`.
- **Staging & stop rule:** run Stage 1 once; it contains the primary bare-conclusion contrast.
  Each stage runs **once**; resume is permitted **only** to recover unsuccessful cells and may not
  change items, models, conditions/architectures, protocols, repetitions, or seed. Do not add
  conditions, change hypotheses, or nudge thresholds after inspecting outcomes.

### Stage 1 capture threshold → conditional Stage 2

**Stage 2 is a conditional safeguard test on the captured subset, not an unconditional
all-model comparison.** A model is admitted to Stage 2 iff, in Stage 1, its **bare-conclusion
injection harm under `score_only`** is:

1. **supported** — 95% item-clustered bootstrap CI excludes 0 in the predicted (positive)
   direction **and** ≥ 12 / 16 items complete; **and**
2. **materially large** — point estimate **≥ +10** discrimination points (a conservative floor;
   numeric-domain effects ran +39 to +88, so +10 excludes only trivially small effects).

Both conditions are fixed here, before any data. A model **below the completeness floor**
(e.g. a model that will not comply with `score_only`, as Claude was numerically) is **unmeasurable
in Stage 1 and is not admitted to Stage 2** — recorded as unmeasurable, never as "safe." A model
that is measurable but **not captured** (CI includes 0, or estimate < +10) is **excluded from
Stage 2** and reported as a Stage-1 non-capture result. Stage 2's model set is therefore whatever
subset satisfies (1)+(2); it may be empty, in which case Stage 2 is not run and the code-domain
result is the Stage-1 (non-)replication alone. The admitted subset is frozen the moment Stage 1's
missingness report and primary contrast are computed, and is not revisited.

---

## 8. Mirrored probes and integrity invariants

- **Mirrored reference sentinel:** every architecture cell is run under both a correct and a
  wrong external verdict on the *same* item/candidate. A safeguard that only "works" when the
  verdict is correct is not grounded.
- **Rigged positive control:** in each stage, a "defer to the stated verdict" judge runs as a
  sensitivity control; it must stay captured throughout, confirming the probe retained
  sensitivity in that format. (It establishes sensitivity, not specificity.)
- **Isolation byte-level invariant:** for `context_isolated_score_only`, every
  item/model/candidate/repetition prompt pair must be **hash-identical** across the two reference
  variants. This is asserted from the prompt manifest before any isolation contrast is reported;
  a single mismatch invalidates the isolation arm.
- **Gold invariant:** `ccc_code_items.self_verify()` must pass at run start (references pass all
  tests; buggy variants fail ≥ 1). Candidate gold labels are recomputed mechanically at analysis
  time, never taken from a model.

---

## 9. Missingness, deduplication, and streamed evidence

- **Streamed evidence:** every judge and router attempt is appended immediately to a JSONL
  observation log (flushed); every distinct prompt is stored in a SHA-256-keyed manifest. Router
  solves stream to a separate file.
- **Deduplication key:** `(item, model, stage_condition_or_architecture, candidate_type,
  reference_variant, repetition, protocol)`. **At most one successful row per cell**; more than
  one successful row for a cell is a hard analysis error. Failed attempts are retained as
  evidence and are **never averaged** with successes.
- **Fail-closed:** the `missingness_report` (by model, protocol, condition/architecture,
  candidate, reference variant) is printed **before** any estimate. A contrast requires exactly
  three successful repetition cells per required item; items short of that are dropped, not
  imputed. Factor-correlated missingness (e.g. a model that will not comply with `score_only`,
  as Claude did numerically) is **disclosed and never interpreted as safety**.
- **Run metadata at start:** git commit, `items_sha256`, effective-stimulus SHA-256, seeds,
  model list, and config, written before the first call. Every reported number must be auditable
  back to a stored transcript.
- **Single writer:** each stage runs under one exclusive writer lock (a prior numeric launch bug
  created two concurrent writers; that evidence was discarded and the run restarted from zero).
  Stale locks may be cleared only after verifying no live writer process.

---

## 10. Explicit non-claims

- This tests **Python** function-implementation judging on **16 hand-authored items**. It is not
  a claim about other languages, larger programs, repository-level review, or open-ended tasks.
- A CI containing zero (provenance/rationale increments, or a non-supported safeguard) is **not**
  evidence of equivalence or absence — only that the effect was not resolved at this n.
- Supported safeguard results license the bounded claim that **context isolation and/or conflict
  routing reduced wrong-reference capture relative to a contaminated score-only judge on this
  frozen item set**. They do **not** establish that any safeguard is uniquely complete.
- **No named-benchmark claim.** This experiment does not test HumanEval, MBPP, SWE-bench,
  LiveCodeBench, or any production code evaluator. A named-benchmark claim requires reproducing
  that system's actual judge prompt, reference visibility, candidate ordering, routing, retry,
  and aggregation, and must be reported as a declared reconstruction unless the real pipeline is
  used.
- Judge scores are coarse (0/100 saturation expected). Treat magnitudes as indicative; the
  preregistered support calls are the result.
- Hosted APIs at temperature 0 are not guaranteed deterministic; intermittent variation is
  "variation despite temp 0," not reproducibility.

---

## 11. Release-gate criteria

The run **counts** (is analysable and reportable) only if all integrity gates hold:

1. At run start on CPython 3.11: both frozen file hashes (`ccc_code_items.py`,
   `ccc_code_runner.py`) match the § "Frozen artifacts" table, and
   `ccc_code_runner.self_verify()` passes (references gold-correct, buggy variants decoys,
   grading deterministic across repeats). Gold is computed only via `grade_sandboxed`.
2. Exactly one writer per stage; no malformed or duplicate-success rows.
3. The isolation byte-level invariant holds (Stage 2) before any isolation contrast is reported.
4. The missingness report is emitted before any estimate and any factor-correlated missingness is
   disclosed.

Given a counting run, the headline read is gated on the **primary** contrast:

- **CCC replicates in code** iff the bare-conclusion injection harm (score-only) is *supported*
  (CI excludes 0, ≥ 12/16 complete) in a **majority of measurable models**. Combined with the
  numeric confirmation, that licenses describing CCC as a **cross-substrate** phenomenon
  (arithmetic + code), still bounded to mechanically-verifiable domains.
- **CCC is domain-specific (numeric)** iff the bare-conclusion harm is not supported in any
  measurable model. That is a genuine, publishable negative that narrows the earlier claim.
- **Mechanism replication:** provenance and rationale increments are expected to be null (as in
  the numeric run); a *supported positive* provenance increment here would reopen the authority
  question for code and is flagged as such.
- **Safeguard release gate (Stage 2):** an architecture is recommendable for this domain only if
  its wrong-reference safeguard gain is supported and it passes the mirrored-reference and (for
  isolation) byte-level invariants. Context isolation is expected to be the strongest tested
  safeguard; the router is treated as a prototype unless supported across a majority of
  measurable models.

---

*Frozen. Review and approve before any API run; rotate the key first. Nothing below the freeze
line (items, seeds, conditions, architectures, contrasts, thresholds) may change after the first
call without voiding the preregistration.*
