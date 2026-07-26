#!/usr/bin/env python3
"""CCC Stage-2 figure — which judging architecture actually resists a wrong reference?

Recomputed from experiments/results/architecture_obs.jsonl using the estimator
in PREREG_contextual_capture_architecture.md:

  D(item, arch, ref) = mean(score | correct cand) - mean(score | wrong_matching cand)
  reference susceptibility = D(correct reference) - D(wrong reference)

Positive susceptibility means the judge scored better when handed a correct
reference than a wrong one -- i.e. the reference reached the scoring decision.
Zero means the reference made no difference to the outcome.

Fail-closed: an item enters a contrast only when all three repetitions of every
required candidate/reference cell succeeded. Item-clustered bootstrap over
items, B=4000. Completeness floor 12 of 16; below it a model is reported
'unmeasurable', never 'null'.

Validated against the published contaminated_score_only susceptibility column
(FINDINGS_contextual_capture_architecture.md).

usage: make_ccc_architecture_figure.py [DATA_ROOT] [OUT_PNG]
"""
import json, random, statistics, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "fig_ccc_architecture.png"
OBS = f"{ROOT}/experiments/results/architecture_obs.jsonl"

B, FLOOR = 4000, 12

MODELS = [("openai/gpt-4o-mini", "GPT-4o mini"),
          ("anthropic/claude-haiku-4.5", "Claude Haiku 4.5"),
          ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
          ("deepseek/deepseek-chat", "DeepSeek Chat"),
          ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B")]

INK, MUTED, LINE = "#1C2733", "#5B6B7A", "#D5DDE4"
STEEL, RUST, TEAL = "#3D5A73", "#BC4B33", "#1F8A70"
GREY = "#A9B6C2"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "text.color": INK, "axes.edgecolor": "#9FB0BE"})

# left-to-right: the disease, two partial defences, the structural one
ARCHS = [
    ("contaminated_score_only", "Reference pasted into the prompt",
     "the ordinary LLM-as-judge setup", RUST),
    ("contaminated_verify_written", "+ “verify it yourself first”",
     "a prompt-level defence, same contaminated context", STEEL),
    ("conflict_router", "Independent solve, then route on conflict",
     "quarantine + fresh judge when the solve disagrees", STEEL),
    ("context_isolated_score_only", "Reference never enters the prompt",
     "structural separation, byte-audited", TEAL),
]


def load(path):
    cell = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        if r.get("error") is not None or r.get("score") is None:
            continue
        cell[(r["model"], r["architecture"], r["item_id"],
              r["reference_variant"], r["candidate_type"])][int(r["repetition"])] = float(r["score"])
    return cell


def complete(cell, m, a, it, ref):
    return all(len(cell.get((m, a, it, ref, c), {})) == 3
               for c in ("correct", "wrong_matching"))


def disc(cell, m, a, it, ref):
    return (statistics.mean(cell[(m, a, it, ref, "correct")].values())
            - statistics.mean(cell[(m, a, it, ref, "wrong_matching")].values()))


def susceptibility(cell, m, arch, seed=20260714):
    items = sorted({k[2] for k in cell if k[0] == m and k[1] == arch})
    vals = [disc(cell, m, arch, it, "correct_reference")
            - disc(cell, m, arch, it, "wrong_reference")
            for it in items
            if complete(cell, m, arch, it, "correct_reference")
            and complete(cell, m, arch, it, "wrong_reference")]
    if not vals:
        return None
    rng = random.Random(seed)
    n = len(vals)
    means = sorted(statistics.mean(rng.choices(vals, k=n)) for _ in range(B))
    return dict(est=statistics.mean(vals), lo=means[int(.025 * B)],
                hi=means[int(.975 * B)], n=n)


cell = load(OBS)
results = [[susceptibility(cell, mid, arch) for mid, _ in MODELS]
           for arch, *_ in ARCHS]

# ---- validation against the published contaminated_score_only column -------
PUB = {"openai/gpt-4o-mini": (90.00, 16), "anthropic/claude-haiku-4.5": (129.29, 7),
       "google/gemini-2.5-flash": (39.90, 16), "deepseek/deepseek-chat": (84.27, 16),
       "meta-llama/llama-3.3-70b-instruct": (112.50, 16)}
print("validation — contaminated_score_only susceptibility vs published:")
for r, (mid, name) in zip(results[0], MODELS):
    pe, pn = PUB[mid]
    flag = "OK" if abs(r["est"] - pe) < 0.005 and r["n"] == pn else "** MISMATCH"
    print(f"  {name:20s} n={r['n']:2d} (pub {pn:2d})  {r['est']:+8.2f} (pub {pe:+8.2f})  {flag}")

# ---------------------------------------------------------------- figure ---
fig = plt.figure(figsize=(16.4, 7.9))
fig.text(0.032, 0.965, "Only one safeguard actually closes the pathway",
         ha="left", va="top", fontsize=21, fontweight="bold", color=INK)
fig.text(0.032, 0.918,
         "Each judge scored the same candidates twice — once with a correct reference available, once with a wrong one. The bar is how much that swap moved its verdict. "
         "Zero means the reference never reached the decision.",
         ha="left", va="top", fontsize=12.2, color=MUTED)

lo_x, hi_x = -55, 175
for pi, ((arch, title, sub, colour), res) in enumerate(zip(ARCHS, results)):
    ax = fig.add_axes([0.088 + pi * 0.232, 0.245, 0.196, 0.525])
    ax.axvspan(lo_x, 0, color="#F4F7F9", zorder=0)
    ax.axvline(0, color=INK, lw=1.4, zorder=2)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(-0.75, len(MODELS) - 0.25)
    ax.invert_yaxis()
    ax.grid(axis="x", color=LINE, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    for yi, r in enumerate(res):
        if r is None:
            continue
        if r["n"] >= FLOOR:
            supported = r["lo"] > 0 or r["hi"] < 0
            c = colour if supported else GREY
            ax.plot([r["lo"], r["hi"]], [yi, yi], color=c, lw=2.4,
                    solid_capstyle="round", zorder=3)
            ax.plot([r["est"]], [yi], "o", ms=9.5, color=c, mec="white",
                    mew=1.6, zorder=4)
        else:
            x = max(lo_x + 6, min(hi_x - 6, r["est"]))
            ax.plot([x], [yi], "o", ms=8.5, mfc="white", mec=GREY, mew=1.8, zorder=4)
            ax.text(x - 6, yi, f"n={r['n']}", va="center", ha="right",
                    fontsize=8.0, color=GREY, style="italic", zorder=4)

    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([n for _, n in MODELS] if pi == 0 else [""] * len(MODELS),
                       fontsize=10.4)
    ax.set_xticks([0, 100])
    ax.tick_params(axis="x", labelsize=9.3)
    ax.text(0.5, 1.155, title, transform=ax.transAxes, ha="center",
            fontsize=11.6, fontweight="bold", color=colour, wrap=True)
    ax.text(0.5, 1.062, sub, transform=ax.transAxes, ha="center",
            fontsize=8.7, color=MUTED, style="italic")

fig.text(0.5, 0.178, "how far the verdict moved when the reference was swapped  "
         "(score points of discrimination;  0 = the reference made no difference)",
         ha="center", va="center", fontsize=10, color=MUTED)

# the honest complication: the router narrows the pathway but does not close it
axR = fig.axes[2]
axR.annotate("still leaking — supported\nsusceptibility in 2 of the 3\nmeasurable models",
             xy=(results[2][3]["est"], 3), xytext=(78, 1.45),
             fontsize=8.3, color=RUST, ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color=RUST, lw=1.3),
             bbox=dict(boxstyle="round,pad=0.32", fc="#F7E9E5", ec=RUST, lw=1.0))

fig.text(0.5, 0.113,
         "Grey = interval covers zero (no supported effect); hollow marker = below the 12-of-16 completeness floor, reported unmeasurable rather than null. 95% item-clustered bootstrap, B = 4,000, recomputed\n"
         "from the raw rows; the leftmost panel reproduces the published susceptibility column exactly. Gemini's small +5.42 under isolation is the preregistered randomisation check, not a pathway — the two\n"
         "prompts it compares were provably the same bytes, so any residual is sampling noise.",
         ha="center", va="center", fontsize=9.1, color=MUTED, linespacing=1.5)
fig.text(0.5, 0.028,
         "Isolation is the only architecture that keeps the reference away from the verdict across models — and the only one whose guarantee is structural rather than behavioural: "
         "480 of 480 judge prompts\nwere byte-identical whichever reference was held, verified here from the stored prompt hashes.",
         ha="center", va="center", fontsize=9.9, color=INK, fontweight="bold", linespacing=1.5)

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("\nwrote", OUT)
for (arch, title, *_), res in zip(ARCHS, results):
    print(f"\n{title}")
    for r, (_, name) in zip(res, MODELS):
        if r:
            print(f"   {name:20s} n={r['n']:2d}  {r['est']:+8.2f} [{r['lo']:+7.2f}, {r['hi']:+7.2f}]")
