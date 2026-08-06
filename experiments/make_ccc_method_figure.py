#!/usr/bin/env python3
"""CCC method figure (paper register) — Figure 1 for the paper's Method section.

Same three panels, same measured values and same source rows as
make_ccc_explainer_figure.py; only the vocabulary differs. That script is the
outreach edition ("crib sheet", "the grader"); this one uses the paper's terms
(reference, judge, candidate, discrimination) and is the one to cite in §4.

Every number on it is measured, not illustrative: GPT-4o mini, the same 16
questions in all three panels, mean score over items x 3 repetitions, taken from
architecture_obs.jsonl.

  panel 1  reference in the prompt, and it is CORRECT   70.0 vs  6.6
  panel 2  reference in the prompt, and it is WRONG      6.2 vs 32.8   (inverted)
  panel 3  reference never enters the prompt            49.2 vs 16.7   (holds)

usage: make_ccc_explainer_figure.py [DATA_ROOT] [OUT_PNG]
"""
import json, statistics, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "fig_ccc_method.png"

INK, MUTED, LINE = "#1C2733", "#5B6B7A", "#D5DDE4"
STEEL, RUST, TEAL, GREY = "#3D5A73", "#BC4B33", "#1F8A70", "#A9B6C2"
RUSTSOFT, TEALSOFT = "#F7E9E5", "#E4F2EE"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "text.color": INK})


def measured():
    ok = defaultdict(dict)
    for line in open(f"{ROOT}/experiments/results/architecture_obs.jsonl"):
        r = json.loads(line)
        if r["model"] != "openai/gpt-4o-mini" or r.get("score") is None:
            continue
        ok[(r["architecture"], r["item_id"], r["reference_variant"],
            r["candidate_type"])][r["repetition"]] = float(r["score"])
    out = {}
    for arch in ("contaminated_score_only", "context_isolated_score_only"):
        items = sorted({k[1] for k in ok if k[0] == arch})
        for ref in ("correct_reference", "wrong_reference"):
            cs, ws = [], []
            for it in items:
                c = ok.get((arch, it, ref, "correct"), {})
                w = ok.get((arch, it, ref, "wrong_matching"), {})
                if len(c) == 3 and len(w) == 3:
                    cs.append(statistics.mean(c.values()))
                    ws.append(statistics.mean(w.values()))
            out[(arch, ref)] = (statistics.mean(cs), statistics.mean(ws), len(cs))
    return out


M = measured()
PANELS = [
    ("(a)  Exposed reference, correct",
     "The judge receives the task, one candidate, and a correct\nreference answer in the same prompt.",
     M[("contaminated_score_only", "correct_reference")], "in-prompt", TEAL,
     "Discrimination is high: the correct candidate scores well above the wrong one."),
    ("(b)  Exposed reference, wrong",
     "Identical except that the reference is wrong. Candidates,\ntask and prompt template are unchanged.",
     M[("contaminated_score_only", "wrong_reference")], "in-prompt", RUST,
     "Discrimination inverts: the wrong candidate now scores higher."),
    ("(c)  Context-isolated, wrong reference",
     "The reference is withheld. The judge scores the candidate\nunaided; nothing is compared for it.",
     M[("context_isolated_score_only", "wrong_reference")], "isolated", TEAL,
     "Discrimination is preserved and invariant to the reference variant."),
]

fig = plt.figure(figsize=(16.2, 8.6))
fig.text(0.03, 0.972, "Figure 1.  Contextual Conclusion Capture and the isolation control",
         ha="left", va="top", fontsize=20, fontweight="bold", color=INK)
# No descriptive sub-line here: the paper's caption carries it, and printing both
# reads as an editing slip. The in-card title stays so the figure survives being
# lifted out of the paper.


def box(ax, x, y, w, h, text, ec, fc="white", fs=9.2, weight="bold", tc=None, ls="solid", lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.5",
                                linewidth=lw, edgecolor=ec, facecolor=fc, linestyle=ls, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight=weight, color=tc or ec, zorder=4)


for pi, (title, sub, (cor, wro, n), mode, accent, verdict) in enumerate(PANELS):
    ax = fig.add_axes([0.035 + pi * 0.325, 0.075, 0.29, 0.855])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    ax.text(0, 99, title, fontsize=13.4, fontweight="bold", color=INK, ha="left", va="top")
    ax.text(0, 92.5, sub, fontsize=9.5, color=MUTED, ha="left", va="top", linespacing=1.45)

    # ---- what the grader is given -------------------------------------
    inp = accent if mode == "in-prompt" else STEEL
    ax.add_patch(Rectangle((4, 60), 92, 20.5, facecolor="#F7F9FA",
                           edgecolor=LINE, lw=1.2, zorder=1))
    ax.text(50, 78.2, "JUDGE PROMPT CONTENTS", fontsize=8.2, color=MUTED,
            ha="center", va="center", fontweight="bold")
    box(ax, 7, 65.5, 26, 9, "task", STEEL, fs=9.0)
    box(ax, 37, 65.5, 26, 9, "candidate", STEEL, fs=9.0)
    if mode == "in-prompt":
        box(ax, 67, 65.5, 26, 9, "reference", accent,
            fc=(TEALSOFT if accent is TEAL else RUSTSOFT), fs=8.8)
    else:
        box(ax, 67, 65.5, 26, 9, "reference\nWITHHELD", GREY, fc="white",
            ls=(0, (3, 2)), fs=8.4, tc=GREY)

    # the quarantined route, panel 3 only — sits under the input strip, no collision
    if mode == "isolated":
        ax.add_patch(FancyBboxPatch((4, 54.0), 92, 5.0,
                                    boxstyle="round,pad=0.3,rounding_size=1.0",
                                    linewidth=1.3, edgecolor=TEAL, facecolor=TEALSOFT,
                                    zorder=2))
        ax.text(50, 56.5, "480 / 480 prompts byte-identical across variants",
                ha="center", va="center", fontsize=8.3, color=TEAL,
                fontweight="bold", zorder=3)

    ay0 = 53.5 if mode == "isolated" else 59.5
    ax.add_patch(FancyArrowPatch((50, ay0), (50, 53.5 if mode != "isolated" else 53.6),
                                 arrowstyle="-|>", mutation_scale=14, linewidth=1.7,
                                 color=STEEL, zorder=3) if mode != "isolated" else
                 FancyArrowPatch((50, 53.8), (50, 53.7), arrowstyle="-",
                                 linewidth=0.1, color="white", zorder=1))
    box(ax, 33, 44, 34, 9.5, "JUDGE", INK, fs=10.6)
    ax.add_patch(FancyArrowPatch((50, 43.5), (50, 37.5), arrowstyle="-|>",
                                 mutation_scale=14, linewidth=1.7, color=STEEL, zorder=3))

    # ---- the two scores it gives --------------------------------------
    ax.text(50, 34.5, "MEAN SCORE  (0–100)", fontsize=8.2, color=MUTED,
            ha="center", va="center", fontweight="bold")

    def bar(y, val, colour, label):
        x0, span = 30, 62
        ax.add_patch(Rectangle((x0, y), span, 6.4, facecolor="#F1F4F6",
                               edgecolor="none", zorder=2))
        ax.add_patch(Rectangle((x0, y), span * val / 100.0, 6.4, facecolor=colour,
                               edgecolor="none", zorder=3))
        ax.text(x0 - 2.5, y + 3.2, label, ha="right", va="center", fontsize=9.0,
                color=colour, fontweight="bold")
        ax.text(x0 + span * val / 100.0 + 2, y + 3.2, f"{val:.1f}", ha="left",
                va="center", fontsize=9.4, color=colour, fontweight="bold")

    bar(24.0, cor, TEAL, "correct\ncandidate")
    bar(14.0, wro, RUST, "wrong\ncandidate")

    # ---- the verdict ---------------------------------------------------
    gap = cor - wro
    vcol = RUST if gap < 0 else TEAL
    ax.add_patch(FancyBboxPatch((4, 1.5), 92, 8.6,
                                boxstyle="round,pad=0.4,rounding_size=1.2",
                                linewidth=1.5, edgecolor=vcol,
                                facecolor=RUSTSOFT if gap < 0 else TEALSOFT, zorder=3))
    ax.text(50, 7.4, f"discrimination  D = {gap:+.1f}", ha="center", va="center",
            fontsize=10.2, color=vcol, fontweight="bold", zorder=4)
    ax.text(50, 3.6, verdict, ha="center", va="center", fontsize=7.8,
            color=INK, zorder=4)

fig.text(0.5, 0.026,
         "Discrimination D = mean score(correct candidate) \u2212 mean score(wrong candidate) is the estimand throughout \u00a7\u00a75\u20137. D > 0 indicates the judge separates correct from incorrect; "
         "D < 0 indicates inversion.\nUnder isolation, D is 32.5 with a wrong reference and 32.7 with a correct one \u2014 the structural guarantee, not a behavioural one: all 480 isolated judge prompts "
         "were byte-identical across reference variants.",
         ha="center", va="center", fontsize=9.0, color=MUTED, linespacing=1.55)

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("wrote", OUT)
for (t, _, (c, w, n), *_ ) in PANELS:
    print(f"  {t:44s} n={n}  right={c:5.1f}  wrong={w:5.1f}  gap={c-w:+6.1f}")
