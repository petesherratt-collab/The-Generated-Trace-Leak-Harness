# CCC figure set

## Two sets, split by register — not by content

The figures divide into a **paper set** and an **outreach set**. Two pairs are the
same figure in two vocabularies; never publish both members of a pair together.

| paper (technical) | outreach (plain) | same data? |
|---|---|---|
| `fig_ccc_method.png` | `fig_ccc_explainer.png` | identical |
| `fig_ccc_openrouter.png` | `fig_ccc_reversal_plain.png` | identical |
| `fig_ccc_mechanism.png` | — | paper only |
| `fig_ccc_frontier.png` | — | paper only |
| `fig_ccc_architecture.png` | — | paper only |

### Paper placement

Five figures, each immediately **before** the table it illustrates. Keep the
tables: for a preregistered paper the table is the result and the figure is the
aid, and the completeness counts that carry the most careful reasoning
(Claude at n=7, n=4, n=2) are not readable off a chart.

| Figure | § | Table it fronts |
|---|---|---|
| 1 `fig_ccc_method.png` | §4 Method | — (no table; this is the missing schematic) |
| 2 `fig_ccc_mechanism.png` | §5 | mechanism-check tables |
| 3 `fig_ccc_frontier.png` | §6.4 | frontier harm table |
| 4 `fig_ccc_openrouter.png` | §6.5 | four-arm model-family table |
| 5 `fig_ccc_architecture.png` | §7 | susceptibility / safeguard table |

**Done.** All five are placed, each with a caption and a "(Figure N)" cross-reference
earned in the prose of §§4–7.

---

## Outreach: the audience-proof pair

For an audience you cannot characterise in advance — including people who have
never thought about LLM evaluation — show **two figures** and stop.

| # | Figure | Answers | Register |
|---|---|---|---|
| 1 | `fig_ccc_explainer.png` | *What is being measured, what goes wrong, what fixes it* | plain |
| 2 | `fig_ccc_reversal_plain.png` | *Is it one grader, or general?* — four graders, and SQL **inverts** | plain |

These two are a complete argument on their own, and they share one vocabulary:
the triptych closes on "the gap between them", and that gap is exactly what the
reversal figure's axis plots. Neither says *discrimination*, *capture*,
*bootstrap* or *supported effect*.

**Add a third only if the audience is choosing what to build:**
`fig_ccc_architecture.png` — the obvious defences ("tell the judge to check its
work", "route around conflicts") do not fully work. Partly redundant with
triptych panel 3, which already shows isolation holding.

**The technical pair, for a paper or a reviewer:** `fig_ccc_mechanism.png` and
`fig_ccc_frontier.png`. Both are excellent and neither is for a newcomer — the
mechanism figure in particular requires reading two near-zero panels as a
positive finding, which is a trained skill.

`fig_ccc_openrouter.png` is the technical-register twin of
`fig_ccc_reversal_plain.png`: identical data, estimator and validation, paper
wording. Use one or the other, never both.

Figure 1 replaces the seven method flow diagrams in `docs/`, which stay as
supporting material.

---

Every figure covers one of the paper's main claims. Every one is **recomputed from the
raw `*_obs.jsonl` rows**, not transcribed from the findings tables, and every one
prints a validation block checking its estimates against the published numbers.

```bash
python3 experiments/make_all_ccc_figures.py      # regenerate all seven + validate
```

The driver exits non-zero if any figure stops reproducing its published values,
so the figures cannot silently drift away from the findings.

## The set

| Figure | Paper | Claim it carries | Evidence |
|---|---|---|---|
| `fig_ccc_method.png` | §4 | **Paper register.** Triptych: exposed-correct → exposed-wrong (inverts) → isolated (holds), defining D as the estimand for §§5–7 | `architecture_obs.jsonl` |
| `fig_ccc_explainer.png` | — | **Outreach register.** Same three panels, same numbers, plain vocabulary | `architecture_obs.jsonl` |
| `fig_ccc_mechanism.png` | §5 | The conflicting **conclusion itself** is the active ingredient — a rationale and a solver label add nothing measurable on top | `provinj_obs_confirmatory.jsonl` |
| `fig_ccc_frontier.png` | §6.4 | Capture survives at the frontier tier; **SQL** is the common failure across every measurable judge | `ccc_frontier_v3_{arith,code,sql}_obs.jsonl` |
| `fig_ccc_reversal_plain.png` | §6.5 | Plain-language twin of the row below — same data, same estimator, newcomer wording | `ccc_openrouter_*/…_obs.jsonl` |
| `fig_ccc_openrouter.png` | §6.5 | One wrong reference answer **reverses** SQL judging in three of four open-weight arms | `ccc_openrouter_*/…_obs.jsonl` |
| `fig_ccc_architecture.png` | §7 | Only **context isolation** closes the pathway; written verification and the router narrow it but leave it open | `architecture_obs.jsonl` |

## Validation status

Every point estimate below is reproduced to the last digit by the script that
draws it.

| Figure | Checks | Result |
|---|---:|---|
| method (paper) | — | every number measured from the rows, none illustrative |
| explainer (outreach) | — | same values as the method figure, plain wording |
| mechanism | 13 | all reproduce, including Claude's `n=2` / `n=4` complete-item counts |
| frontier | 11 | all reproduce |
| openrouter | 12 | all reproduce |
| reversal (plain) | 12 | all reproduce — same estimator as openrouter |
| architecture | 5 | all reproduce, including Claude's `n=7` |

The architecture script additionally re-derives the byte audit from the stored
prompt hashes rather than quoting it: all **480 / 480** isolated-architecture
prompt pairs are hash-identical across reference variants, 0 differing.

## House rules for figure text

Four rounds of review found the same three faults recurring across different
figures. They are rules, not per-figure fixes.

1. **A strap states what the whole figure shows; a callout states what one
   panel shows.** "Capture survives at the frontier" over a panel with 4 of 12
   cells supported, or "one wrong reference can flip a judge's verdict" over
   nine cells where nothing flips, is a claim the figure does not carry. If the
   striking result is confined to one panel, the strap says so.
2. **No sentence appears both inside a figure and in its caption.** Figure text
   serves someone looking at the chart; the caption serves someone reading the
   prose. Duplication reads as an editing slip in print. Where a figure carries
   its own banner, the caption records what the *design* is doing — the shared
   scale, the nesting of contrasts, the auditable floors — which is what a
   reader cannot recover from the picture.
3. **Every non-obvious encoding is stated once, in the figure.** Shaded regions,
   colour assignments, and the direction a line runs are not self-evident. If a
   careful reader has to ask what the pale band means, it needs a line of text —
   including when the answer is "nothing much".
4. **A claim the reader is meant to count should be countable off the figure.**
   The "three of four cross zero" claim was correct and still misread, because
   four markers had to be judged by eye against a shaded half-panel. Printing
   the value beside each marker removed the ambiguity. Prefer this over trusting
   the geometry.
5. **The support rule is not a licence.** §7.1 establishes that an interval
   excluding zero by a few points can be noise. A figure must not label such an
   estimate "supported" when the paper's own limitation section asks readers to
   discount it.

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
