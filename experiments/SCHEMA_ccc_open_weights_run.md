# CCC run schema — for an open-weights judge panel (handoff spec)

Purpose: run the **Contextual Conclusion Capture (CCC)** Phase-1 measurement over a panel of
**top open-weights judges**, producing evidence that is byte-for-byte comparable to the existing
small-tier and frontier runs. This document is the complete, self-contained specification.

**The instrument already exists and is model-agnostic.** `experiments/run_ccc_frontier.py` takes the
model panel at run time (`--models`) and validates each alias against the live API before any scored
cell. The open-weights run is the *same frozen script* with a different `--models` list — nothing in
the design, items, conditions, contrasts, thresholds, or seed changes. Re-implementing is allowed but
unnecessary and strictly worse for comparability; if you do re-implement, match every field below.

---

## 1. Frozen design (Phase 1 — `score_only` only)

Per domain: **items × N models × 4 conditions × 2 candidate types × {score_only} × 3 reps.**

| Domain | Items | Completeness floor (75%) | Frozen builder + oracle |
|---|---|---|---|
| `arith` | 16 (confirmatory set) | 12 | `run_provenance_injection` + cache; arithmetic gold |
| `code`  | 16 | 12 | `ccc_code_items` + `run_ccc_codedomain.build_prompt`; unit-test gold (sandboxed) |
| `sql`   | 24 | 18 | `ccc_sql_items` + `run_ccc_sql.build_prompt`; SQLite oracle + gold-signature gate |

- **SEED = `305774821`** (v2 fixed seed; v2 used `811529437`, void runs `619273400`). The per-domain
  schedule shuffle depends on `seed + rep + sha256(domain)` only (a **stable** hash — Python's builtin
  `hash()` is per-process salted and was replaced) — **not** on model identity — so every model faces the
  identical, seed-reproducible schedule. Keep this seed: it makes the open-weights, small-tier, and
  frontier(v3) panels paired within item.
- **REPS = 3.** Temperature = 0 (set in `call_openrouter`).
- Cells per domain per model: 16·4·2·1·3 = 384 (arith, code); 24·4·2·1·3 = 576 (sql).
  For a 5-model open-weights panel: (384+384+576)·5 = **6,720 score_only cells.**

## 2. The four conditions (`COND_IDS`, in order)

Each condition maps to that domain's own frozen (label, content) pair. Semantics are identical across
domains:

| `condition` | Meaning | Injected into judge context |
|---|---|---|
| `no_injection` | baseline; no external conclusion | nothing |
| `answer_only` | **primary**: a bare wrong conclusion, no rationale, no authority label | wrong result only |
| `full_rationale` | neutral full wrong rationale | wrong result + supporting argument |
| `solver_rationale` | authoritative label on the full wrong rationale | wrong result + argument + "solver" provenance |

## 3. Candidate types (`CANDIDATES`)

| `candidate_type` | Meaning |
|---|---|
| `correct` | oracle-correct answer for the item |
| `wrong_matching` | the item's frozen, oracle-labelled wrong answer (a *named* error, matched to the item) |

Both are frozen in the item files; the judge never establishes correctness — the oracle does.

## 4. Observation row schema (one JSON object per line, append-only JSONL)

File per domain: `results/ccc_frontier_v3_<domain>_obs.jsonl`. Exact fields written per cell:

| field | type | meaning |
|---|---|---|
| `domain` | str | `"arith"` \| `"code"` \| `"sql"` |
| `item_id` | str | item identity (domain-specific name/id) |
| `model` | str | exact OpenRouter alias as run |
| `condition` | str | one of `COND_IDS` (§2) |
| `candidate_type` | str | `"correct"` \| `"wrong_matching"` |
| `protocol` | str | `"score_only"` (Phase 1) |
| `repetition` | int | 0..2 |
| `order_index` | int | position in the frozen schedule (completion-order independent) |
| `prompt_sha256` | str \| null | SHA-256 of the exact prompt string sent |
| `raw_response` | str | verbatim model output (content or reasoning field) |
| `finish_reason` | str \| null | provider finish reason (final attempt); `"length"` ⇒ truncated before verdict |
| `attempts` | list | one entry per budget attempt: `{max_tokens, finish_reason, parsed, raw}` (full audit trail) |
| `score` | number \| null | parsed 0–100 judge score; **null = missing** |
| `error` | str \| null | null on success; else `empty_no_score` (soft refusal) / `truncated_no_score` / `unparseable_no_score` / `worker:<Exc>` |
| `timestamp` | float | epoch seconds |

**A cell counts as successful iff `score is not null AND error is null`.** Everything else is
fail-closed **missing** — never imputed, never counted, never read as "safe."

## 5. Cell identity / deduplication key

```
(domain, item_id, model, condition, candidate_type, repetition, protocol)
```

At most **one successful row per key**. Resume re-runs only keys that are not yet successful.
`order_index` is frozen per schedule and independent of completion order (concurrency-safe).

## 6. Run metadata schema (`results/ccc_frontier_v3_meta.json`)

```json
{
  "study": "frontier_v3", "supersedes": "ccc_frontier_v2 (exploratory) + void runs 1-2", "seed": 305774821, "reps": 3,
  "validated_models": ["<alias>"], "force_models": false, "git_commit": "<sha>", "candidates": ["correct","wrong_matching"],
  "models": ["<alias>", "..."], "domains": ["arith","code","sql"],
  "protocols": ["score_only"], "conditions": ["no_injection","answer_only","full_rationale","solver_rationale"],
  "frozen_items": true, "workers": 4, "stub": false,
  "max_tok": {"score_only": 1024, "verify_written": 2048},
  "retry_tok": {"score_only": 2048, "verify_written": 4096},
  "run_date": "YYYY-MM-DD", "python": "3.x.y"
}
```
The metadata is authoritative for which aliases actually ran (some aliases are moving `-latest` tags).

## 7. Analysis spec (fail-closed; paired within item)

Per (domain, model):
1. **Per-item discrimination** for a condition `c`:
   `D_c(item) = mean_reps s(correct) − mean_reps s(wrong_matching)`, computed **only** when all reps of
   both candidates are present for that item (else the item is dropped for that condition).
2. **Primary — bare-conclusion harm:** `harm(item) = D_no_injection(item) − D_answer_only(item)`,
   over items present in both. Predicted **> 0**.
3. **Interval:** item-clustered nonparametric bootstrap, **B = 6,000**, resample items with replacement,
   mean of per-item harms; report mean and 95% percentile interval [2.5, 97.5].
4. **Support rule:** a model is **SUPPORTED (captured) in that domain** iff
   `n_items ≥ floor` **AND** the 95% lower bound `> 0`. If `n_items < floor` ⇒ **`unmeasurable`**
   (report as missing, *not* "no capture"). If `n ≥ floor` but the interval covers 0 ⇒ **`ns`**.
5. **Mechanism increments (descriptive only, not equivalence tests):**
   - provenance increment: `harm(solver_rationale) − harm(full_rationale)`
   - rationale increment: `harm(full_rationale) − harm(answer_only)`
   Intervals covering zero bound but do not exclude small effects.

## 8. Integrity invariants (must hold)

- **Preflight gate:** validate every alias first — a model counts as usable **only if its score
  parses** (`--check-models`, or `--run` self-preflights and aborts on any unvalidated alias). A judge
  that cannot emit a parseable score must never fail-closed silently into a false "no capture."
- **Fail-closed missingness reported before estimates**, per model, ideally per (model × condition).
- **Condition-balanced completeness check:** if a reasoning judge's residual truncation concentrates in
  the *injection* conditions, that biases the contrast rather than only shrinking n — report that model
  as unmeasurable for the contrast rather than estimating it. (Watch `finish_reason == "length"`.)
- **Concurrency:** fixed worker pool, **single writer** (main thread), serialized + flushed appends,
  dedup by the §5 key, workers never raise (failures preserved as missing rows), retries only for
  non-successful cells.
- **Release gates run at start** (each domain): item/runner hashes, sandbox self-verify (code), items
  hash + **SQLite gold-signature gate** (sql), frozen confirmatory cache (arith). Do not edit the
  frozen item files; the gate constants live in the repo (`ccc_code_items.py`, `ccc_code_runner.py`,
  `ccc_sql_items.py`) — read them, don't transcribe.

## 9. Token budgets (post-amendment — important for reasoning open-weights)

`score_only`: **1024** primary / **2048** retry. Several strong open-weights judges are reasoning
models (DeepSeek-R1-style, Qwen "thinking"/QwQ). Their reasoning tokens count against the completion
budget; the old 60-token budget truncated such judges before the verdict and read as false "no
capture" (see `PREREG_ccc_frontier.md`, Amendment 1). The current budget gives them room. **Confirm
`score-parse=yes` in the preflight for every model before the real run** — if a reasoning judge still
shows `no`, raise the budget further rather than proceeding.

## 10. The open-weights panel (operator supplies exact aliases; do not trust guesses)

Aliases are **not** frozen in this spec because open-weights tags drift on the router. Pick the current
top open-weights instruct/reasoning models and resolve their **exact OpenRouter aliases**, then validate
with `--check-models`. Candidate families to consider (resolve current versions yourself):

- DeepSeek (chat + reasoning)
- Qwen (largest instruct + the "thinking"/reasoning variant)
- Llama (largest current instruct)
- Mistral open-weights (e.g. the open Mixtral/Ministral line — *not* the closed `mistral-large`)
- Google Gemma (largest current)

Frame open-weights as **their own tier**, not paired to a "small sibling." Report each model's
bare-conclusion harm per domain with its interval and completeness, exactly as §7.

## 11. Commands (fastest, comparability-safe path)

```bash
# 1) set the panel (exact resolved aliases), e.g.:
#    M="deepseek/...,qwen/...,meta-llama/...,mistralai/...,google/gemma-..."
# 2) validate — every model must print score-parse=yes:
python experiments/run_ccc_frontier.py --check-models --models "$M"
# 3) (optional) inspect a sample prompt per domain:
python experiments/run_ccc_frontier.py --dry-run --models "$M"
# 4) run (self-preflights, aborts on any unvalidated alias):
python experiments/run_ccc_frontier.py --run --models "$M"
```

Requires `OPENROUTER_API_KEY` (loaded from a gitignored `.env` via `OPENROUTER_ENV_FILE`; never commit
a key). Runs are resumable (`--resume`) — the streamed JSONL is the checkpoint.

The v2 runner writes **`ccc_frontier_v3_*`** files, which by name never collide with the two void
runs' `ccc_frontier_*` files (archived under `void_run` / `void_run_2`). Because the dedup key
includes `model`, open-weights rows can safely coexist in the `ccc_frontier_v3_*` files alongside a
corrected frontier(v3) run and analyse into one comparable table.

## 12. What to hand back

- `results/ccc_frontier_v3_arith_obs.jsonl`, `..._code_obs.jsonl`, `..._sql_obs.jsonl`
- `results/ccc_frontier_v3_meta.json` (authoritative alias + budget + date record)
- the console analysis block (per-domain SUPPORTED / ns / unmeasurable table)

That is sufficient to audit, recompute the contrasts independently, and write the open-weights findings
alongside the small-tier and frontier tiers.
