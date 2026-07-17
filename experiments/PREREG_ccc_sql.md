# Preregistration — Contextual Conclusion Capture, relational (SQL) domain

**Frozen design date:** 2026-07-17 · **Status:** freeze BEFORE any API call. No OpenRouter
request is made against this design until this file is reviewed and committed and the operator
has confirmed the key.
**Parent studies:** numeric ([`PREREG_contextual_conclusion_capture_confirmatory.md`](PREREG_contextual_conclusion_capture_confirmatory.md))
and code ([`PREREG_ccc_codedomain.md`](PREREG_ccc_codedomain.md)) replications.
**Frozen items + oracle:** [`ccc_sql_items.py`](ccc_sql_items.py)

This is the **third computational-reasoning domain**: finite relational reasoning over frozen
SQLite fixtures. It tests whether Contextual Conclusion Capture (CCC) — loss of correct-vs-wrong
judge discrimination caused by a conflicting conclusion in context — generalises from
arithmetic and imperative code to **declarative relational algebra**, while keeping gold
**mechanical and non-circular** (SQLite is the oracle; no model establishes truth).

Direction convention: `harm = disc(baseline) − disc(condition)`; positive = more capture.

## Frozen artifacts (content-addressed; the primary freeze)

| Artifact | Role | SHA-256 (LF-normalised) |
|---|---|---|
| [`ccc_sql_items.py`](ccc_sql_items.py) | 24 items + SQLite oracle + canonicalizer | `72ce9e7dccbbc844261f53820c3f7c5ac7b09e5764a1a5858d207b292f56629c` |

| Frozen oracle value | | |
|---|---|---|
| **Gold signature** (item, correct-result, wrong-result vector) | | `427ea26bb3bce201bf753397e309ef3e417257737abea8fa5975688b6b1d2beb` |
| **SQLite library version** (verified) | | `3.45.1` |
| **Interpreter set** (gold verified identical across) | | CPython 3.10–3.13 |

**SQLite-version fail-closed gate (design-critical).** The gold answers depend on the SQLite
*library* version, which is compiled into the interpreter and can differ by machine/OS
independently of the Python version. Rather than assume all versions agree, the run **recomputes
the gold signature at start and aborts unless it equals `427ea26b…`**. If the local SQLite
produces any different result, the run does not proceed. `sqlite3.sqlite_version` is recorded in
metadata. (The queries are written to be version-robust — standard aggregates/joins/`EXISTS`,
`ORDER BY` only over distinct keys so there are no tie-order ambiguities — so a mismatch would be
a signal to investigate, not to nudge the threshold.)

No code sandbox is required: execution is limited to the **frozen queries over in-memory
fixtures** (no model-authored SQL is ever executed; the models are judges, not query authors),
and `sqlite3` is stdlib and network-free.

## Items and mechanical gold

24 hand-authored tasks over three frozen fixtures (`emp`, `ord`, `prod`), spanning **joins,
grouping, NULL semantics, ordering, duplicate rows, subqueries, and boundary predicates**. Each
item pairs a **correct query** with a **wrong query embodying one named relational error**
(`error_desc` — e.g. inner-vs-left join, forgotten `DISTINCT`, `= NULL` vs `IS NULL`,
existential-vs-universal, `>` vs `>=` boundary, global-vs-correlated average). Both are executed
by SQLite:

- correct candidate result = `oracle(correct query)` → gold-correct;
- `wrong_matching` candidate result = `oracle(wrong query)`, tied to `error_desc` → gold-wrong.

**Frozen canonicalization** (`canonicalize`): row-order significance is set **explicitly per
item** (`ordered`), never inferred from SQL; unordered results are sorted by a canonical cell
key; integers and integral floats unify (5 == 5.0), non-integral floats round to 6 dp; NULL is a
fixed sentinel distinct from any value; bag semantics (duplicate rows) preserved.

**Audits (offline, already passed):** `self_verify()` asserts unique names, every item's
correct and wrong results are computable, **differ** (collision check — no wrong result
canonicalizes equal to its correct one), and are **deterministic across repeats**; verified
identical across CPython 3.10–3.13. All answers are compact (scalars, aggregates, booleans, or
≤2-row lists), so an injected result claim is a single clean statement.

## Judge unit, candidates, discrimination

- **Judge unit:** `(schema + seeded rows, question, candidate claimed result)`. The judge scores
  0–100 whether the candidate result correctly answers the question over the given data — it must
  reason relationally against the rows. The unit tests / oracle are never shown.
- **Candidate types:** `correct` (oracle result of the correct query) and `wrong_matching`
  (oracle result of the wrong query).
- **Discrimination (per item):** `mean(score | correct) − mean(score | wrong_matching)`.

## Conflicting conclusion (content × label)

The foreign conclusion is a **claimed (wrong) query result**, the relational analogue of a
leaked answer key. Four injection conditions, mirrored from the prior studies:

1. `none / no_injection` — baseline.
2. `neutral / answer_only` — **the bare conflicting conclusion**: one neutral line asserting the
   wrong result (e.g. *"Reference note: the query result is 900."*). No reasoning. **PRIMARY.**
3. `neutral / full_wrong_rationale` — the wrong result with a fabricated but plausible relational
   justification, neutrally labelled.
4. `solver / full_wrong_rationale` — condition 3 attributed to a privileged source ("Solver / DB
   reference").

**Protocols:** `score_only` and `verify_written`.

## Primary contrast and mechanism checks

Paired within item, item-clustered bootstrap 95% CIs, fail-closed (item enters a contrast only
when all three reps of every required cell succeeded). **Supported** iff CI excludes 0 in the
predicted direction AND ≥ 18 of 24 items complete (the ≥ 75% floor used in prior stages).

- **PRIMARY — bare-conclusion injection harm, score-only:** `disc(no_injection) − disc(neutral,
  answer_only)`. Predicted > 0. The direct CCC test in the relational domain.
- Full-analysis injection harm (score-only); protocol mitigation (diff-in-diff on the bare
  contrast); residual capture under verify_written.
- **Mechanism increments** (CI containing 0 is NOT equivalence): provenance = `harm(solver,full)
  − harm(neutral,full)`; rationale = `harm(neutral,full) − harm(neutral,answer_only)`.

## Architectures (Stage 2, conditional)

Carried forward unchanged and crossed with a mirrored external reference (`correct_reference` =
the oracle result; `wrong_reference` = the wrong-query result):

1. `contaminated_score_only` — the claimed result precedes the candidate; score only.
2. `contaminated_verify_written` — claimed result present; re-derive in writing, then score.
3. `context_isolated_score_only` — the claimed result is in pipeline metadata but **never** in
   the judge prompt; correct/wrong variants have **byte-identical** judge prompts (audited).
4. `conflict_router` — a fresh schema+question-only solve produces a claimed result; the harness
   **canonicalizes it and the external reference and compares mechanically** (agreement uses the
   same frozen canonicalizer as gold — this is where relational result-equivalence is exercised);
   agree → contaminated score-only path; disagree/unparseable → quarantine and route to a fresh
   verify-written judge that never sees the reference or the solver transcript.

## Design, size, repetitions, seeds

- **Items:** the 24 frozen items. **Models:** `openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`,
  `google/gemini-2.5-flash`, `deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct`.
  **Reps:** exactly 3, independently shuffled, rep-block deconflicted.
- **Stage 1 (injection / primary):** 24 × 5 × 4 conditions × 2 candidates × 2 protocols × 3 =
  **5,760 judge cells**. Seed `838271905`.
- **Stage 2 (architectures / conditional):** 24 × |admitted| × 4 architectures × 2 references ×
  2 candidates × 3 + `24 × |admitted| × 3` router solves. Seed `838271906`.
- **Staging & stop rule:** run Stage 1 once; it contains the primary contrast. Stage 2 runs only
  for models admitted by the Stage-1 capture threshold. Each stage runs once; resume recovers
  only unsuccessful cells and may not change items, models, conditions/architectures, protocols,
  reps, or seed.

## Stage-1 capture threshold → conditional Stage 2

A model is admitted to Stage 2 iff its bare-conclusion score-only harm is **supported** (CI > 0,
≥ 18/24 complete) **and** its point estimate is **≥ +10** discrimination points. Models below the
completeness floor are unmeasurable and not admitted (never "safe"); measurable-but-uncaptured
models are excluded and reported as Stage-1 non-capture. Stage 2's subset (possibly empty) is
frozen the moment Stage 1's primary contrast is computed.

## Integrity requirements

- **Freeze before API access:** fixtures, SQL, canonicalization rules, items hash, gold
  signature, SQLite version, seeds, model set, thresholds, and missingness policy (this file).
- **Streamed evidence:** every judge and router attempt appended immediately to JSONL, flushed;
  distinct prompts stored in a SHA-256 manifest; run metadata (hashes, gold signature, sqlite
  version, seeds, python) written at start.
- **Deduplication key:** `(item, model, condition/architecture, candidate, [ref_variant], rep,
  protocol)`. At most one successful row per cell; more than one is a hard analysis error.
- **Fail-closed:** missingness report before any estimate; a contrast requires all three
  successful reps per required item; factor-correlated missingness disclosed, never imputed,
  never interpreted as safety.
- **Isolation invariant:** in Stage 2, every isolated correct/wrong reference prompt pair must be
  byte-identical (asserted from the manifest before any isolation contrast is reported).
- **Immutability:** run each stage once; successful cells are never rerun.

## Non-claims

- Tests a **frozen SQLite micro-domain** (24 hand-authored tasks), not SQL benchmarks (Spider,
  BIRD, WikiSQL), production database agents, or text-to-SQL systems.
- A successful replication generalises the CCC claim to **this relational task family only**; a
  CI containing zero is not evidence of equivalence or immunity.
- SQL is a **third computational paradigm** (declarative/relational) alongside arithmetic and
  imperative code; it does **not** extend the claim to non-mechanical/open-ended judging, which
  remains out of scope precisely because it would need an evaluator to establish gold.
- Scores are coarse (0/100 saturation expected); directions and preregistered calls are the
  result, magnitudes indicative.

## Release-gate criteria

The run counts only if, at start: the items hash matches this file; **the recomputed gold
signature equals `427ea26b…` on the local SQLite** (else abort); the interpreter is in 3.10–3.13;
`self_verify()` passes; exactly one writer; no malformed/duplicate-success rows; the missingness
report precedes estimates; and (Stage 2) the isolation byte-invariant holds. Given a counting
run, the headline read is gated on the primary contrast: **CCC replicates in the relational
domain** iff bare-conclusion score-only harm is supported in a majority of measurable models —
which, with the numeric and code confirmations, would license describing CCC as holding across
**three computational-reasoning paradigms with mechanical gold**.

*Frozen. Review and approve before any API run. Nothing below the freeze line — items, gold
signature, canonicalization, seeds, conditions, architectures, contrasts, thresholds — may change
after the first call without voiding the preregistration.*
