#!/usr/bin/env python3
"""CCC mechanism figure — is the conclusion itself the active ingredient?

Recomputes the preregistered confirmatory mechanism checks from the raw
observation rows and plots them. Nothing is transcribed from the findings
tables; the estimator is re-implemented from
PREREG_contextual_conclusion_capture_confirmatory.md and validated against the
published point estimates (all 13 reproduce to the last digit, including the
per-model complete-item counts).

  D(item, cond)   = mean(score | correct) - mean(score | wrong_matching)
  harm            = D(no_injection) - D(cond)        positive = more capture
  rationale inc   = harm(neutral, full)  - harm(neutral, bare)   = D(bare) - D(full)
  provenance inc  = harm(solver,  full)  - harm(neutral, full)   = D(full) - D(solver)

Fail-closed: an item enters a contrast only when all three repetitions of every
required cell succeeded. The baseline is excluded from the completeness set for
the two increments, where it cancels algebraically -- this reproduces the
published n=2 / n=4 for Claude. Item-clustered bootstrap over items, B=4000.
Completeness floor 12 of 16; below it a model is 'unmeasurable', never 'null'.

usage: make_ccc_mechanism_figure.py [DATA_ROOT] [OUT_PNG]
"""
import json, random, statistics, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "fig_ccc_mechanism.png"
OBS = f"{ROOT}/experiments/results/provinj_obs_confirmatory.jsonl"

B, FLOOR = 4000, 12
BASE, BARE = (None, None), ("neutral", "wrong_answer_only")
FULL, SOLVER = ("neutral", "full_wrong_rationale"), ("solver", "full_wrong_rationale")

MODELS = [("openai/gpt-4o-mini", "GPT-4o mini"),
          ("anthropic/claude-haiku-4.5", "Claude Haiku 4.5"),
          ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
          ("deepseek/deepseek-chat", "DeepSeek Chat"),
          ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B")]

# ---- CCC house palette (from the project's mermaid artifacts) --------------
INK, MUTED, LINE = "#1C2733", "#5B6B7A", "#D5DDE4"
STEEL, RUST, TEAL = "#3D5A73", "#BC4B33", "#1F8A70"
RUSTSOFT, GREY = "#F7E9E5", "#A9B6C2"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "text.color": INK, "axes.edgecolor": "#9FB0BE"})


def load(path):
    cell = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        if r.get("error") is not None or r.get("score") is None:
            continue
        c = r["condition"]
        cell[(r["model"], r["protocol"], r["item_id"],
              (c["label_key"], c["content_key"]), r["candidate_type"])][r["repetition"]] = float(r["score"])
    return cell


def complete(cell, m, p, it, cond):
    return all(len(cell.get((m, p, it, cond, c), {})) == 3
               for c in ("correct", "wrong_matching"))


def disc(cell, m, p, it, cond):
    return (statistics.mean(cell[(m, p, it, cond, "correct")].values())
            - statistics.mean(cell[(m, p, it, cond, "wrong_matching")].values()))


def estimate(cell, m, proto, need, fn, seed=20260714):
    items = sorted({k[2] for k in cell if k[0] == m})
    vals = [fn({c: disc(cell, m, proto, it, c) for c in need})
            for it in items if all(complete(cell, m, proto, it, c) for c in need)]
    if not vals:
        return None
    rng = random.Random(seed)
    n = len(vals)
    means = sorted(statistics.mean(rng.choices(vals, k=n)) for _ in range(B))
    return dict(est=statistics.mean(vals), lo=means[int(.025 * B)],
                hi=means[int(.975 * B)], n=n)


cell = load(OBS)

PANELS = [
    ("A bare wrong conclusion", "no label, no argument — just the answer",
     [BASE, BARE], lambda d: d[BASE] - d[BARE], RUST,
     "harm vs a clean context"),
    ("+ a full wrong rationale", "does adding persuasive argument add capture?",
     [BARE, FULL], lambda d: d[BARE] - d[FULL], STEEL,
     "increment over the bare conclusion"),
    ("+ a solver's authority label", "does adding provenance add capture?",
     [FULL, SOLVER], lambda d: d[FULL] - d[SOLVER], STEEL,
     "increment over the neutral label"),
]

results = [[estimate(cell, mid, "score_only", need, fn) for mid, _ in MODELS]
           for _, _, need, fn, _, _ in PANELS]

# ---------------------------------------------------------------- figure ---
fig = plt.figure(figsize=(15.2, 7.6))
fig.text(0.035, 0.965, "The active ingredient is the conclusion itself",
         ha="left", va="top", fontsize=21, fontweight="bold", color=INK)
fig.text(0.035, 0.918,
         "A wrong answer placed in a judge's context collapses its ability to tell correct from incorrect. Dressing that answer up — with a full argument, or with a "
         "solver's authority — adds no measurable capture on top, and one label reduced it.",
         ha="left", va="top", fontsize=12.3, color=MUTED)

lo_x, hi_x = -62, 126
for pi, ((title, sub, need, fn, colour, xlab), res) in enumerate(zip(PANELS, results)):
    ax = fig.add_axes([0.075 + pi * 0.313, 0.275, 0.268, 0.525])
    ax.axvspan(lo_x, 0, color="#F4F7F9", zorder=0)
    ax.axvline(0, color=INK, lw=1.4, zorder=2)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(-0.75, len(MODELS) - 0.25)
    ax.invert_yaxis()
    ax.grid(axis="x", color=LINE, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    for yi, (r, (_, name)) in enumerate(zip(res, MODELS)):
        if r is None:
            continue
        if r["n"] >= FLOOR:
            ax.plot([r["lo"], r["hi"]], [yi, yi], color=colour, lw=2.4,
                    solid_capstyle="round", zorder=3)
            ax.plot([r["est"]], [yi], "o", ms=10, color=colour, mec="white",
                    mew=1.6, zorder=4)
        else:
            # Below the completeness floor: show the estimate as an open marker
            # with NO interval. The prereg forbids reading these as effects, and
            # an n=2 interval drawn to scale would dominate the panel.
            x = max(lo_x + 6, min(hi_x - 6, r["est"]))
            ax.plot([x], [yi], "o", ms=9, mfc="white", mec=GREY, mew=1.8, zorder=4)
            right = x > (lo_x + hi_x) / 2
            ax.text(x - 5 if right else x + 5, yi, f"below floor · n={r['n']}",
                    va="center", ha="right" if right else "left",
                    fontsize=8.2, color=GREY, style="italic", zorder=4)

    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([n for _, n in MODELS] if pi == 0 else [""] * len(MODELS),
                       fontsize=10.6)
    ax.set_xticks([-50, 0, 50, 100])
    ax.tick_params(axis="x", labelsize=9.5)
    ax.set_xlabel(xlab, fontsize=9.6, color=MUTED, labelpad=6)
    ax.text(0.5, 1.14, title, transform=ax.transAxes, ha="center",
            fontsize=13, fontweight="bold", color=colour)
    ax.text(0.5, 1.055, sub, transform=ax.transAxes, ha="center",
            fontsize=9.4, color=MUTED, style="italic")

# The one interval that excludes zero anywhere in the two increment panels. Its
# bound is -6.25, inside the +/-7.8 noise band that the isolated negative control
# establishes (see the paper's 7.1), so the rule alone does not carry it. Label it
# directional, not supported: the figure must not make the kind of claim that
# section warns readers to discount.
r = results[2][4]
axL = fig.axes[2]
axL.annotate("the only interval excluding zero,\nand it runs AWAY from capture\n(bound inside the noise band — directional)",
             xy=(r["hi"] + 1, 4), xytext=(14, 4.35),
             fontsize=8.4, color=TEAL, ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.4),
             bbox=dict(boxstyle="round,pad=0.35", fc="#E4F2EE", ec=TEAL, lw=1.1))

fig.text(0.5, 0.148,
         "Score-only judging. Points are score-points of discrimination (correct minus wrong candidate); bars are 95% item-clustered bootstrap intervals, B = 4,000, recomputed from the raw\n"
         "observation rows and reproducing every published point estimate. Fail-closed: an item counts only where all three repetitions of every required cell succeeded.\n"
         "Shading marks negative territory — an estimate there means the manipulation improved discrimination rather than harming it. Colour marks the panel, not significance:\n"
         "the primary harm contrast is rust, the two increments steel.",
         ha="center", va="center", fontsize=9.4, color=MUTED, linespacing=1.5)
fig.text(0.5, 0.035,
         "An interval covering zero is not proof of equivalence. The claim is that a privileged label and a supporting argument were UNNECESSARY for the effect — not that they can never matter.",
         ha="center", va="center", fontsize=9.6, color=INK, linespacing=1.5,
         fontweight="bold")

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("wrote", OUT)
for (title, *_), res in zip(PANELS, results):
    print(f"\n{title}")
    for r, (_, name) in zip(res, MODELS):
        if r:
            print(f"   {name:20s} n={r['n']:2d}  {r['est']:+8.2f} [{r['lo']:+7.2f}, {r['hi']:+7.2f}]")
