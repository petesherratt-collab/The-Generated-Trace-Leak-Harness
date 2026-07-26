# CCC figure set

**The five.** One methodology figure and four results figures, in narrative order.
A reader who knows nothing about the subject should be able to go 1 → 5 and
follow the whole argument.

| # | Figure | Answers |
|---|---|---|
| 1 | `fig_ccc_explainer.png` | *What is being measured, what goes wrong, and what fixes it* |
| 2 | `fig_ccc_openrouter.png` | *Does it really happen?* — yes, SQL judging **inverts** |
| 3 | `fig_ccc_mechanism.png` | *Why?* — the bare conclusion is the active ingredient |
| 4 | `fig_ccc_frontier.png` | *Only cheap models?* — no, frontier too |
| 5 | `fig_ccc_architecture.png` | *So what do I do?* — only isolation closes the pathway |

Figure 1 replaces the seven separate method flow diagrams in `docs/`. Those stay
as supporting material; they are not part of the five.

---

Every figure covers one of the paper's main claims. Every one is **recomputed from the
raw `*_obs.jsonl` rows**, not transcribed from the findings tables, and every one
prints a validation block checking its estimates against the published numbers.

```bash
python3 experiments/make_all_ccc_figures.py      # regenerate all four + validate
```

The driver exits non-zero if any figure stops reproducing its published values,
so the figures cannot silently drift away from the findings.

## The set

| Figure | Paper | Claim it carries | Evidence |
|---|---|---|---|
| `fig_ccc_explainer.png` | §4 | Triptych: the grader works with a correct reference, **inverts** with a wrong one, and holds when the reference is kept out of the prompt | `architecture_obs.jsonl` |
| `fig_ccc_mechanism.png` | §5 | The conflicting **conclusion itself** is the active ingredient — a rationale and a solver label add nothing measurable on top | `provinj_obs_confirmatory.jsonl` |
| `fig_ccc_frontier.png` | §6.4 | Capture survives at the frontier tier; **SQL** is the common failure across every measurable judge | `ccc_frontier_v3_{arith,code,sql}_obs.jsonl` |
| `fig_ccc_openrouter.png` | §6.5 | One wrong reference answer **reverses** SQL judging in three of four open-weight arms | `ccc_openrouter_*/…_obs.jsonl` |
| `fig_ccc_architecture.png` | §7 | Only **context isolation** closes the pathway; written verification and the router narrow it but leave it open | `architecture_obs.jsonl` |

## Validation status

Every point estimate below is reproduced to the last digit by the script that
draws it.

| Figure | Checks | Result |
|---|---:|---|
| explainer | — | every number measured from the rows, none illustrative |
| mechanism | 13 | all reproduce, including Claude's `n=2` / `n=4` complete-item counts |
| frontier | 11 | all reproduce |
| openrouter | 12 | all reproduce |
| architecture | 5 | all reproduce, including Claude's `n=7` |

The architecture script additionally re-derives the byte audit from the stored
prompt hashes rather than quoting it: all **480 / 480** isolated-architecture
prompt pairs are hash-identical across reference variants, 0 differing.

## Conventions held across the set

- **Fail-closed.** An item enters a contrast only when all three repetitions of
  every required cell succeeded. Failed attempts are never averaged in.
- **Item-clustered bootstrap**, B = 4,000, 95% intervals.
- **Completeness floors** are the frozen per-experiment values (12 of 16; 18 of 24
  for SQL). A model below its floor is drawn as a hollow marker and labelled
  *unmeasurable* — never as a null result.
- **Injection-skewed missingness** fails the balance safeguard and is reported
  unmeasurable regardless of the nominal estimate. This is what removes Claude
  Fable from the frontier code and SQL panels.
- **An interval covering zero is not evidence of equivalence.** The mechanism
  figure says so on its face, because that is the reading its two null panels
  most invite.
- Shared x-scale within a figure. Rescaling a near-zero panel to fill its axes
  would manufacture an effect that the data does not show.
- Palette follows the CCC mermaid diagrams in `docs/`: steel `#3D5A73`,
  rust `#BC4B33`, teal `#1F8A70`.

## Not yet built

- **Cross-tier comparison** (13 models over frontier / open-weight / cost tiers).
  Blocked on a read-only normaliser projecting the older cost-tier condition
  encoding into the v3 schema, plus an audit of `reliability_key` across every
  cost-tier file. Both must be settled before a combined panel is trustworthy;
  tiers were never randomised, so any such figure is descriptive only.
- **Missingness** (§8) is currently carried by tables. It only needs a figure if
  the paper leads with it.
