#!/usr/bin/env python3
"""CCC §6.5 figure — one wrong reference answer can flip a judge's verdict.

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
OUT = sys.argv[2] if len(sys.argv) > 2 else "fig_ccc_openrouter.png"
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
print("validation vs paper §6.5 harm table:")
for k, pe in PUB.items():
    r = res[k]
    print(f"  {k[0]:16s} {k[1]:6s} n={r['n']:2d} harm={r['harm']:+8.2f} (paper {pe:+8.2f}) "
          f"{'OK' if abs(r['harm']-pe) < 0.005 else '** MISMATCH'}")

# ---------------------------------------------------------------- figure ---
fig = plt.figure(figsize=(15.0, 8.0))
fig.text(0.035, 0.966, "One wrong reference answer moves every judge \u2014 in SQL it reverses three of four",
         ha="left", va="top", fontsize=21, fontweight="bold", color=INK)
fig.text(0.035, 0.921,
         "Each line is one model in one task type. It starts where the judge scored with a clean context, and ends where the same judge scored with a single wrong "
         "reference answer added. Nothing else changed.",
         ha="left", va="top", fontsize=12.1, color=MUTED)

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
        # value beside the injected marker: the crossing claim in the caption is
        # countable here, rather than judged by eye against the shaded half-panel
        left = r["inj"] < r["base"]
        ax.text(r["inj"] + (-4.5 if left else 4.5), yi - 0.30,
                f'{r["inj"]:+.0f}', va="center", ha="right" if left else "left",
                fontsize=8.0, color=RUST, fontweight="bold", zorder=6)
        if r["supported"]:
            ax.text(min(108, max(r["base"], r["inj"]) + 5), yi, "captured",
                    va="center", fontsize=8.2, color=RUST, fontweight="bold")

    if dom == "sql":
        # bottom-left: the top-left corner collides with Qwen's value label
        ax.text(-106, len(ARMS) - 0.42, "REVERSED\nprefers the WRONG answer", fontsize=8.6,
                color=RUST, fontweight="bold", va="center", ha="left", linespacing=1.3)

    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([a for a, _ in ARMS] if pi == 0 else [""] * len(ARMS), fontsize=10.5)
    if pi == 0:
        for yi, (arm, _) in enumerate(ARMS):
            if arm.startswith(("MiniMax", "GLM")):
                ax.text(-0.012, yi + 0.30, "reasoning off \u00b7 0 tokens",
                        transform=ax.get_yaxis_transform(), ha="right", va="center",
                        fontsize=7.4, color=TEAL, style="italic")
    ax.set_xticks([-100, -50, 0, 50, 100])
    ax.tick_params(axis="x", labelsize=9.2)
    ax.text(0.5, 1.055, dtitle, transform=ax.transAxes, ha="center",
            fontsize=13.5, fontweight="bold", color=INK)

fig.text(0.5, 0.185, "Can the judge tell a correct answer from a wrong one?",
         ha="center", va="center", fontsize=11.4, color=INK)
fig.text(0.5, 0.146,
         "+100 = always ranks the correct answer above the wrong one     ·     0 = cannot tell them apart     ·     below 0 = it ranks the WRONG answer higher\n"
         "A line running LEFT means the wrong reference cost the judge discrimination; a line running RIGHT means it scored higher with the reference than without.",
         ha="center", va="center", fontsize=9.7, color=MUTED)

h = [plt.Line2D([0], [0], marker="o", ls="", ms=9, color=TEAL, mec="white"),
     plt.Line2D([0], [0], marker="o", ls="", ms=9, color=RUST, mec="white"),
     plt.Line2D([0], [0], color=RUST, lw=1.8)]
fig.legend(h, ["clean context", "one wrong reference answer added",
               "95% interval on the injected score"],
           loc="lower center", bbox_to_anchor=(0.5, 0.075), ncol=3,
           frameon=False, fontsize=9.6, handletextpad=0.6, columnspacing=2.2)

fig.text(0.5, 0.030,
         "Recomputed from the raw observation rows (fail-closed; item-clustered bootstrap, B = 4,000); every harm reproduces the paper's §6.5 table. “captured” marks a preregistered supported effect.\n"
         "The four arms ran under different reasoning protocols and are compared descriptively, not pooled. Task difficulty, prompt wording and answer format differ by task type, so magnitudes across\n"
         "the three panels are observed, not causally attributable to the task type itself.",
         ha="center", va="center", fontsize=8.9, color=MUTED, linespacing=1.5)

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("\nwrote", OUT)
