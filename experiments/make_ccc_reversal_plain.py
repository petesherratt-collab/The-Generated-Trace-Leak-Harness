#!/usr/bin/env python3
"""CCC reversal figure, PLAIN-LANGUAGE edition — for a reader meeting this cold.

Same data, same estimator and same validation as make_ccc_openrouter_figure.py;
only the wording differs. Pitched to sit directly after the explainer triptych,
whose closing line is "gap between them" — this figure plots exactly that gap.

The open-weight / OpenRouter model-family extension, rebuilt from the raw
observation rows so the figure is reproducible from the repo rather than
existing only as an exported image.

  D(item, cond) = mean(score | correct) - mean(score | wrong_matching)
  plotted: D(no_injection)  ->  D(answer_only), per model per domain
  harm    = D(no_injection) - D(answer_only)   (the paper's §6.5 table)

D is on a -100..+100 scale: +100 = always ranks the correct candidate above the
wrong one, 0 = cannot tell them apart, below 0 = ranks the WRONG one higher.

Fail-closed, item-clustered bootstrap B=4000 on the injected endpoint.
The four arms ran under different reasoning protocols and are compared
descriptively, not pooled.

usage: make_ccc_openrouter_figure.py [DATA_ROOT] [OUT_PNG]
"""
import json, random, statistics, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "fig_ccc_reversal_plain.png"
B = 4000

ARMS = [
    ("Qwen 3.7 Plus", "ccc_openrouter_v1/ccc_openrouter_v1_qwen37_plus_hosted_bounded_{d}_obs.jsonl"),
    ("Kimi K2.7 Code", "ccc_openrouter_kimi_native_v1/ccc_openrouter_kimi_native_v1_{d}_obs.jsonl"),
    ("MiniMax M3", "ccc_openrouter_minimax_m3_v2/ccc_openrouter_minimax_m3_v2_{d}_obs.jsonl"),
    ("GLM 5.2", "ccc_openrouter_glm52_v2/ccc_openrouter_glm52_v2_{d}_obs.jsonl"),
]
DOMAINS = [("arith", "Arithmetic", 12), ("code", "Python code", 12), ("sql", "SQL", 18)]

INK, MUTED, LINE = "#1C2733", "#5B6B7A", "#D5DDE4"
RUST, TEAL, GREY = "#BC4B33", "#1F8A70", "#A9B6C2"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "text.color": INK, "axes.edgecolor": "#9FB0BE"})


def analyse(path, floor):
    ok = defaultdict(dict)
    for line in open(f"{ROOT}/experiments/results/{path}"):
        r = json.loads(line)
        if r.get("protocol") != "score_only":
            continue
        if r.get("error") is not None or r.get("score") is None:
            continue
        ok[(r["item_id"], r["condition"], r["candidate_type"])][r["repetition"]] = float(r["score"])

    items = sorted({k[0] for k in ok})
    base, inj, harm = [], [], []
    for it in items:
        if all(len(ok.get((it, c, cand), {})) == 3
               for c in ("no_injection", "answer_only")
               for cand in ("correct", "wrong_matching")):
            d = {c: statistics.mean(ok[(it, c, "correct")].values())
                    - statistics.mean(ok[(it, c, "wrong_matching")].values())
                 for c in ("no_injection", "answer_only")}
            base.append(d["no_injection"]); inj.append(d["answer_only"])
            harm.append(d["no_injection"] - d["answer_only"])
    if not harm:
        return None
    rng = random.Random(20260722)
    n = len(harm)
    im = sorted(statistics.mean(rng.choices(inj, k=n)) for _ in range(B))
    hm = sorted(statistics.mean(rng.choices(harm, k=n)) for _ in range(B))
    return dict(base=statistics.mean(base), inj=statistics.mean(inj),
                inj_lo=im[int(.025 * B)], inj_hi=im[int(.975 * B)],
                harm=statistics.mean(harm), harm_lo=hm[int(.025 * B)],
                n=n, supported=(hm[int(.025 * B)] > 0 and n >= floor))


res = {(a, d): analyse(p.format(d=d), floor)
       for a, p in ARMS for d, _, floor in DOMAINS}

PUB = {("Qwen 3.7 Plus", "arith"): 94.17, ("Qwen 3.7 Plus", "code"): -9.27,
       ("Qwen 3.7 Plus", "sql"): 165.28,
       ("Kimi K2.7 Code", "arith"): -11.88, ("Kimi K2.7 Code", "code"): 1.46,
       ("Kimi K2.7 Code", "sql"): 70.69,
       ("MiniMax M3", "arith"): 75.17, ("MiniMax M3", "code"): 19.65,
       ("MiniMax M3", "sql"): 143.68,
       ("GLM 5.2", "arith"): 52.08, ("GLM 5.2", "code"): 13.33,
       ("GLM 5.2", "sql"): 148.61}
print("validation vs paper 6.5 harm table (plain-language edition):")
for k, pe in PUB.items():
    r = res[k]
    print(f"  {k[0]:16s} {k[1]:6s} n={r['n']:2d} harm={r['harm']:+8.2f} (paper {pe:+8.2f}) "
          f"{'OK' if abs(r['harm']-pe) < 0.005 else '** MISMATCH'}")

# ---------------------------------------------------------------- figure ---
fig = plt.figure(figsize=(15.0, 8.0))
fig.text(0.035, 0.968, "It is not one grader, and it is not a small effect",
         ha="left", va="top", fontsize=21.5, fontweight="bold", color=INK)
fig.text(0.035, 0.922,
         "Four different AI graders, three kinds of task. Each line starts where the grader scored with no crib sheet, and ends where the same grader scored after "
         "one wrong crib sheet was added.\nThe further right, the better it tells right answers from wrong ones.",
         ha="left", va="top", fontsize=12.1, color=MUTED, linespacing=1.5)

for pi, (dom, dtitle, floor) in enumerate(DOMAINS):
    ax = fig.add_axes([0.105 + pi * 0.303, 0.265, 0.258, 0.525])
    ax.axvspan(-110, 0, color="#FBF3F1", zorder=0)
    ax.axvline(0, color=INK, lw=1.3, zorder=2)
    ax.set_xlim(-112, 112)
    ax.set_ylim(-0.7, len(ARMS) - 0.3)
    ax.invert_yaxis()
    ax.grid(axis="x", color=LINE, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    for yi, (arm, _) in enumerate(ARMS):
        r = res[(arm, dom)]
        if r is None:
            continue
        ax.plot([r["base"], r["inj"]], [yi, yi], color=GREY, lw=3.0,
                solid_capstyle="round", zorder=2, alpha=0.85)
        ax.plot([r["inj_lo"], r["inj_hi"]], [yi, yi], color=RUST, lw=1.6,
                solid_capstyle="round", zorder=3)
        ax.plot([r["base"]], [yi], "o", ms=9, color=TEAL, mec="white", mew=1.5, zorder=5)
        ax.plot([r["inj"]], [yi], "o", ms=9, color=RUST, mec="white", mew=1.5, zorder=5)
        if r["supported"]:
            ax.text(min(108, max(r["base"], r["inj"]) + 5), yi, "got worse",
                    va="center", fontsize=8.2, color=RUST, fontweight="bold")

    if dom == "sql":
        ax.text(-106, -0.50, "ANYWHERE IN THIS SHADED BAND, THE GRADER HAS IT BACKWARDS\nit marks the wrong answer higher than the right one",
                fontsize=8.4, color=RUST, fontweight="bold", va="center",
                ha="left", linespacing=1.35)

    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([a for a, _ in ARMS] if pi == 0 else [""] * len(ARMS), fontsize=10.5)
    ax.set_xticks([-100, -50, 0, 50, 100])
    ax.tick_params(axis="x", labelsize=9.2)
    ax.text(0.5, 1.055, dtitle, transform=ax.transAxes, ha="center",
            fontsize=13.5, fontweight="bold", color=INK)

fig.text(0.5, 0.188, "How well can the grader tell a right answer from a wrong one?",
         ha="center", va="center", fontsize=11.6, color=INK)
fig.text(0.5, 0.148,
         "+100  it always marks the right answer higher      ·      0  it cannot tell them apart      ·      below 0  it marks the WRONG answer higher",
         ha="center", va="center", fontsize=9.8, color=MUTED)

h = [plt.Line2D([0], [0], marker="o", ls="", ms=9, color=TEAL, mec="white"),
     plt.Line2D([0], [0], marker="o", ls="", ms=9, color=RUST, mec="white"),
     plt.Line2D([0], [0], color=RUST, lw=1.8)]
fig.legend(h, ["no crib sheet", "after one wrong crib sheet",
               "the range the result could plausibly fall in"],
           loc="lower center", bbox_to_anchor=(0.5, 0.075), ncol=3,
           frameon=False, fontsize=9.6, handletextpad=0.6, columnspacing=2.2)

fig.text(0.5, 0.030,
         "Every grader saw the same questions, three times each; the dot is the average and the bar shows how much that average could move. “got worse” marks a drop big enough to be a real effect\n"
         "rather than chance, decided before the data was collected. The four graders ran on different services under their own settings, so they are shown side by side rather than averaged together,\n"
         "and the three task types differ in difficulty and wording — so the gap between panels is something we observed, not something the task type alone caused.",
         ha="center", va="center", fontsize=8.9, color=MUTED, linespacing=1.55)

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("\nwrote", OUT)
