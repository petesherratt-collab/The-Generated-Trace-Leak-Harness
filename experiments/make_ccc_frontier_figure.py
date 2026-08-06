#!/usr/bin/env python3
"""CCC §6.4 figure — does capture survive at the frontier model tier?

Recomputed from the preregistered v3 frontier evidence
(ccc_frontier_v3_{arith,code,sql}_obs.jsonl), which PREREG_ccc_frontier_v3.md
freezes as the confirmatory extension.

  D(item, cond) = mean(score | correct) - mean(score | wrong_matching)
  bare harm     = D(no_injection) - D(answer_only)      positive = more capture

Fail-closed: an item enters the contrast only when all three repetitions of
every required cell succeeded. Item-clustered bootstrap, B=4000. Completeness
floors are the frozen per-domain values (12 of 16 for arith/code, 18 of 24 for
sql). A model whose missingness is concentrated in injected conditions fails the
balance safeguard and is reported UNMEASURABLE regardless of its nominal
estimate -- this is what removes Fable from code and SQL.

usage: make_ccc_frontier_figure.py [DATA_ROOT] [OUT_PNG]
"""
import json, random, statistics, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "fig_ccc_frontier.png"
B = 4000

DOMAINS = [("arith", "Arithmetic", 16, 12), ("code", "Python code", 16, 12),
           ("sql", "SQL", 24, 18)]
MODELS = [("openai/gpt-5.6-sol", "GPT-5.6-sol"),
          ("google/gemini-3.1-pro-preview", "Gemini 3.1 Pro"),
          ("x-ai/grok-4.5", "Grok 4.5"),
          ("~anthropic/claude-fable-latest", "Claude Fable")]

INK, MUTED, LINE = "#1C2733", "#5B6B7A", "#D5DDE4"
STEEL, RUST, TEAL, GREY = "#3D5A73", "#BC4B33", "#1F8A70", "#A9B6C2"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "text.color": INK, "axes.edgecolor": "#9FB0BE"})


def analyse(domain, floor):
    rows = [json.loads(l) for l in
            open(f"{ROOT}/experiments/results/ccc_frontier_v3_{domain}_obs.jsonl")]
    ok = defaultdict(dict)
    miss = defaultdict(lambda: [0, 0])          # model -> [base fails, injected fails]
    for r in rows:
        if r["protocol"] != "score_only":
            continue
        if r.get("error") is not None or r.get("score") is None:
            miss[r["model"]][0 if r["condition"] == "no_injection" else 1] += 1
            continue
        ok[(r["model"], r["item_id"], r["condition"], r["candidate_type"])][r["repetition"]] = float(r["score"])

    out = {}
    for mid, _ in MODELS:
        items = sorted({k[1] for k in ok if k[0] == mid})
        vals = []
        for it in items:
            if all(len(ok.get((mid, it, c, cand), {})) == 3
                   for c in ("no_injection", "answer_only")
                   for cand in ("correct", "wrong_matching")):
                d = {c: statistics.mean(ok[(mid, it, c, "correct")].values())
                        - statistics.mean(ok[(mid, it, c, "wrong_matching")].values())
                     for c in ("no_injection", "answer_only")}
                vals.append(d["no_injection"] - d["answer_only"])
        base_f, inj_f = miss[mid]
        # frozen balance safeguard: missingness concentrated in injected cells
        skewed = (base_f + inj_f) > 0 and inj_f >= 3 * max(base_f, 1) and inj_f >= 10
        if not vals:
            out[mid] = None
            continue
        rng = random.Random(20260720)
        n = len(vals)
        means = sorted(statistics.mean(rng.choices(vals, k=n)) for _ in range(B))
        out[mid] = dict(est=statistics.mean(vals), lo=means[int(.025 * B)],
                        hi=means[int(.975 * B)], n=n, floor=floor,
                        skewed=skewed, base_f=base_f, inj_f=inj_f,
                        measurable=(n >= floor) and not skewed)
    return out


results = {d: analyse(d, floor) for d, _, _, floor in DOMAINS}

PUB = {("arith", "openai/gpt-5.6-sol"): -7.08,
       ("arith", "google/gemini-3.1-pro-preview"): 0.21,
       ("arith", "x-ai/grok-4.5"): -0.52,
       ("arith", "~anthropic/claude-fable-latest"): 62.92,
       ("code", "openai/gpt-5.6-sol"): 11.19,
       ("code", "google/gemini-3.1-pro-preview"): -2.50,
       ("code", "x-ai/grok-4.5"): 1.35,
       ("sql", "openai/gpt-5.6-sol"): 50.59,
       ("sql", "google/gemini-3.1-pro-preview"): 40.91,
       ("sql", "x-ai/grok-4.5"): 27.36,
       ("sql", "~anthropic/claude-fable-latest"): 4.92}
print("validation vs the v3 run output:")
for (dom, mid), pe in PUB.items():
    r = results[dom][mid]
    print(f"  {dom:6s} {mid:32s} n={r['n']:2d} {r['est']:+8.2f} (run {pe:+8.2f}) "
          f"{'OK' if abs(r['est']-pe) < 0.005 else '** MISMATCH'}")

# ---------------------------------------------------------------- figure ---
fig = plt.figure(figsize=(14.6, 7.4))
fig.text(0.035, 0.965, "A stronger tier does not remove capture — it relocates it into SQL",
         ha="left", va="top", fontsize=21, fontweight="bold", color=INK)
fig.text(0.035, 0.918,
         "The preregistered v3 extension, four frontier judges across three mechanically-verifiable domains. A bare wrong answer in context; nothing else changed. "
         "Positive means discrimination degraded; larger means more of it lost.",
         ha="left", va="top", fontsize=12.1, color=MUTED)

lo_x, hi_x = -30, 100
for pi, (dom, dtitle, nitems, floor) in enumerate(DOMAINS):
    ax = fig.add_axes([0.115 + pi * 0.298, 0.245, 0.252, 0.545])
    ax.axvspan(lo_x, 0, color="#F4F7F9", zorder=0)
    ax.axvline(0, color=INK, lw=1.4, zorder=2)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(-0.75, len(MODELS) - 0.25)
    ax.invert_yaxis()
    ax.grid(axis="x", color=LINE, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    for yi, (mid, _) in enumerate(MODELS):
        r = results[dom][mid]
        if r is None:
            continue
        if r["measurable"]:
            supported = r["lo"] > 0
            c = RUST if supported else GREY
            ax.plot([r["lo"], r["hi"]], [yi, yi], color=c, lw=2.4,
                    solid_capstyle="round", zorder=3)
            ax.plot([r["est"]], [yi], "o", ms=9.5, color=c, mec="white",
                    mew=1.6, zorder=4)
        else:
            why = "injection-skewed" if r["skewed"] else f"n={r['n']}<{r['floor']}"
            ax.plot([lo_x + 8], [yi], "o", ms=8.5, mfc="white", mec=GREY,
                    mew=1.8, zorder=4)
            ax.text(lo_x + 13, yi, f"unmeasurable · {why}", va="center",
                    fontsize=8.1, color=GREY, style="italic", zorder=4)

    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([n for _, n in MODELS] if pi == 0 else [""] * len(MODELS),
                       fontsize=10.5)
    ax.set_xticks([0, 50, 100])
    ax.tick_params(axis="x", labelsize=9.4)
    ax.text(0.5, 1.10, dtitle, transform=ax.transAxes, ha="center",
            fontsize=13.5, fontweight="bold", color=INK)
    ax.text(0.5, 1.028, f"{nitems} items · floor {floor}", transform=ax.transAxes,
            ha="center", fontsize=9.2, color=MUTED, style="italic")

fig.text(0.5, 0.176, "score points of discrimination lost when a bare wrong answer was added   "
         "(0 = the injection changed nothing)",
         ha="center", va="center", fontsize=10, color=MUTED)

fig.text(0.5, 0.108,
         "Grey = interval covers zero. Shading marks negative territory: an estimate there means the injection improved discrimination. 95% item-clustered bootstrap, B = 4,000,\n"
         "recomputed from the frozen v3 observation rows; every estimate reproduces the run output exactly. Fable is not resistant in code or SQL — its endpoint returned provider\n"
         "content-filter blocks on 148 code and 27 SQL cells, almost all in injected conditions. Missingness that tracks the treatment biases the surviving contrast, so the frozen\n"
         "balance safeguard reports those cells unmeasurable rather than letting a nominal estimate stand.",
         ha="center", va="center", fontsize=9.1, color=MUTED, linespacing=1.5)
fig.text(0.5, 0.028,
         "SQL is the common failure across every measurable frontier judge — and those three judges come from three different providers. Arithmetic and code are model-specific.",
         ha="center", va="center", fontsize=9.9, color=INK, fontweight="bold")

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("\nwrote", OUT)
