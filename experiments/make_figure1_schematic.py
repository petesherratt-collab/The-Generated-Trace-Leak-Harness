#!/usr/bin/env python3
"""Figure 1 — the design schematic.

Drawn from generated_leak_harness_v15_selfcontained.py, not from the prose:
  observe()            line 449   opacity-attenuated projection of the cause
  eval_generator()     line 867   the four conditions and their (obs, side) targets
  _metrics()           line 928   lift / GROUND-GAP / SHARPEN as cell contrasts
  _eval_isolated()     line 1215  what does and does not cross the process wall

Panel A: the pipeline and the isolation boundary.
Panel B: the 2x2 of blind conditions, and the mirror pairs.
Panel C: each verdict metric as a contrast between specific cells.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = "/home/user/The-Generated-Trace-Leak-Harness/experiments/fig1_design_schematic.png"

NAVY     = "#1f3a5f"
TITLE    = "#12345a"
INK      = "#333333"
MUTED    = "#6b7280"
GRID     = "#d9dde3"
CRIMSON  = "#b3122e"   # the true cause T — hidden
ORANGE   = "#e07b1a"   # the decoy D — hidden
GREEN    = "#2c7a3f"   # the sanctioned observation channel
PURPLE   = "#6a3d9a"   # the side channel (the attack surface)
PINKFILL = "#fbe9e7"
GREENFIL = "#edf6ef"
STEEL    = "#8fa2b7"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "text.color": INK, "figure.dpi": 130,
})

fig = plt.figure(figsize=(15.0, 11.2))
fig.text(0.045, 0.976, "How the harness asks whether a generator is reading the evidence or leaking the answer",
         ha="left", va="top", color=TITLE, fontsize=19.5, fontweight="bold")
fig.text(0.045, 0.945,
         "The true cause is never shown to anything that produces a verdict. It reaches the generator only through one attenuated channel — and on 40% of trials that channel is pointed at a decoy instead.",
         ha="left", va="top", color=MUTED, fontsize=12.2)


def box(ax, x, y, w, h, text, ec=NAVY, fc="white", fs=10.2, weight="bold",
        tc=None, lw=1.6, ls="solid", z=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.4,rounding_size=1.2",
                                linewidth=lw, edgecolor=ec, facecolor=fc,
                                linestyle=ls, zorder=z))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=weight, color=tc or ec, zorder=z + 1)


def arrow(ax, x1, y1, x2, y2, color=NAVY, lw=1.8, ls="-", z=2, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=15, linewidth=lw, color=color,
                                 linestyle=ls, zorder=z,
                                 shrinkA=0, shrinkB=0))


# =====================================================================
# PANEL A — the pipeline
# =====================================================================
axA = fig.add_axes([0.035, 0.545, 0.93, 0.365])
axA.set_xlim(0, 100); axA.set_ylim(-1, 44); axA.axis("off")

axA.text(0, 43.5, "A    the pipeline — and what is allowed to cross the process wall",
         fontsize=12.6, fontweight="bold", color=TITLE, ha="left", va="top")

# --- the world -------------------------------------------------------
box(axA, 1.5, 17, 15.5, 15, "", ec=NAVY, fc="#f7f9fb", lw=1.6)
axA.text(9.2, 30.3, "THE WORLD", ha="center", fontsize=10.4, fontweight="bold", color=NAVY)
axA.text(9.2, 26.2, "a DAG whose multi-step\nhandoff has failed", ha="center",
         fontsize=8.6, color=MUTED, linespacing=1.35)
axA.text(9.2, 22.4, "T  the true broken edge", ha="center", fontsize=9.0,
         color=CRIMSON, fontweight="bold")
axA.text(9.2, 19.9, "D  a decoy edge", ha="center", fontsize=9.0,
         color=ORANGE, fontweight="bold")
axA.text(9.2, 14.6, "both drawn fresh each trial", ha="center",
         fontsize=8.2, color=MUTED, style="italic")

# --- upper lane: evidence -> substrate -------------------------------
arrow(axA, 17.2, 27.0, 23.3, 27.0, color=NAVY)
axA.text(20.2, 28.5, "redact", ha="center", fontsize=8.4, color=MUTED, style="italic")
box(axA, 23.5, 22.5, 15.5, 9.0, "EVIDENCE\nthe cause removed", ec=NAVY, fs=9.4)
arrow(axA, 39.2, 27.0, 45.3, 27.0, color=NAVY)
box(axA, 45.5, 21.9, 17.0, 10.2, "SUBSTRATE  v0.4\nhash-pinned, never edited", ec=NAVY, fs=9.4)
axA.text(54.0, 19.6, "→  baseline blame", ha="center", fontsize=9.0,
         color=NAVY, fontweight="bold")

# --- lower lane: observation -> generator ----------------------------
arrow(axA, 16.0, 18.6, 23.3, 10.4, color=GREEN)
box(axA, 23.5, 4.0, 15.5, 9.6,
    "OBSERVATION CHANNEL\nthe cause projected into\nper-edge features,\nattenuated by opacity",
    ec=GREEN, fc=GREENFIL, fs=8.5, weight="normal", tc=GREEN)
axA.text(31.2, 14.8, "the ONLY sanctioned route", ha="center", fontsize=8.4,
         color=GREEN, fontweight="bold", style="italic")
axA.text(31.2, 1.9, "a side channel is also offered — the attack surface",
         ha="center", fontsize=8.2, color=PURPLE, style="italic")

arrow(axA, 39.2, 8.8, 45.3, 8.8, color=GREEN)

# the isolation wall
axA.plot([43.0, 43.0], [0.2, 17.6], color=NAVY, lw=2.4, ls=(0, (5, 3)), zorder=5)
axA.text(43.0, 18.6, "process wall", ha="center", fontsize=8.8,
         color=NAVY, fontweight="bold", zorder=6)

box(axA, 45.5, 3.6, 17.0, 10.4,
    "GENERATOR\nrebuilt in a fresh interpreter\nemits 4 trace channels per edge",
    ec=PURPLE, fc="white", fs=8.8, weight="normal", tc=PURPLE)
axA.text(54.0, 1.6, "anomaly · confidence · note quality · completeness",
         ha="center", fontsize=7.9, color=MUTED)

# --- converge --------------------------------------------------------
arrow(axA, 62.7, 24.0, 69.0, 21.5, color=NAVY)
arrow(axA, 62.7, 9.8, 69.0, 16.0, color=PURPLE)
box(axA, 69.2, 14.0, 15.5, 10.4, "RE-WEIGHTED\nBLAME", ec=NAVY, fs=10.0)
arrow(axA, 84.9, 19.2, 90.6, 19.2, color=CRIMSON)
box(axA, 90.8, 14.0, 8.6, 10.4, "SCORED\nvs  T", ec=CRIMSON, fc=PINKFILL, fs=9.6, tc=CRIMSON)
axA.text(95.1, 10.6, "in all four\nconditions alike",
         ha="center", fontsize=8.0, color=CRIMSON, linespacing=1.35, style="italic")

# what crosses the wall — parked in free space, bottom right
axA.add_patch(Rectangle((66.0, 0.4), 33.5, 7.4, facecolor="#f4f6f9",
                        edgecolor=GRID, lw=1.2, zorder=1))
axA.text(67.6, 5.9, "crosses the wall", fontsize=8.6, color=GREEN,
         fontweight="bold", ha="left", va="center")
axA.text(67.6, 3.9, "the serialised observation,\nevidence and side channel",
         fontsize=8.0, color=INK, ha="left", va="center", linespacing=1.3)
axA.text(84.4, 5.9, "never crosses", fontsize=8.6, color=CRIMSON,
         fontweight="bold", ha="left", va="center")
axA.text(84.4, 3.7, "T,  D,  and the\ncondition label c",
         fontsize=8.0, color=CRIMSON, ha="left", va="center",
         fontweight="bold", linespacing=1.3)


# =====================================================================
# PANEL B — the 2x2 of blind conditions
# =====================================================================
axB = fig.add_axes([0.035, 0.075, 0.46, 0.415])
axB.set_xlim(0, 100); axB.set_ylim(0, 100); axB.axis("off")
axB.text(0, 99, "B    the four blind conditions — one drawn secretly per trial",
         fontsize=12.6, fontweight="bold", color=TITLE, ha="left", va="top")

gx0, gy0, cw, ch = 26, 26, 31, 25
# column headers (what the SIDE channel points at)
axB.text(gx0 + cw / 2, 85.5, "side → T", ha="center", fontsize=10.2,
         fontweight="bold", color=PURPLE)
axB.text(gx0 + cw * 1.5, 85.5, "side → D", ha="center", fontsize=10.2,
         fontweight="bold", color=PURPLE)
axB.text(gx0 + cw, 91.5, "what the SIDE CHANNEL points at", ha="center",
         fontsize=9.2, color=MUTED, style="italic")
# row headers (what the OBSERVATION points at)
axB.text(gx0 - 3, gy0 + ch * 1.5, "obs → T", ha="right", va="center",
         fontsize=10.2, fontweight="bold", color=GREEN)
axB.text(gx0 - 3, gy0 + ch * 0.5, "obs → D", ha="right", va="center",
         fontsize=10.2, fontweight="bold", color=GREEN)
axB.text(4.5, gy0 + ch, "what the\nOBSERVATION\npoints at", ha="center", va="center",
         fontsize=9.2, color=MUTED, style="italic", rotation=90, linespacing=1.3)

cells = {
    ("T", "T"): ("honest",   "obs and side AGREE", "mirror pair \u2460", GREEN,   GREENFIL),
    ("T", "D"): ("poison",   "they DISAGREE",      "mirror pair \u2461", CRIMSON, PINKFILL),
    ("D", "T"): ("decouple", "they DISAGREE",      "mirror pair \u2461", CRIMSON, PINKFILL),
    ("D", "D"): ("collude",  "obs and side AGREE", "mirror pair \u2460", GREEN,   GREENFIL),
}
pos = {("T", "T"): (0, 1), ("T", "D"): (1, 1), ("D", "T"): (0, 0), ("D", "D"): (1, 0)}
for k2, (ci, ri) in pos.items():
    name, agree, chip, col, fillc = cells[k2]
    x = gx0 + ci * cw
    y = gy0 + ri * ch
    axB.add_patch(Rectangle((x, y), cw - 1.5, ch - 1.5, facecolor=fillc,
                            edgecolor=col, lw=1.7, zorder=2))
    axB.text(x + (cw - 1.5) / 2, y + ch * 0.70, name, ha="center", va="center",
             fontsize=12.0, fontweight="bold", color=col, zorder=3)
    axB.text(x + (cw - 1.5) / 2, y + ch * 0.46, agree, ha="center", va="center",
             fontsize=8.3, color=MUTED, zorder=3, style="italic")
    axB.text(x + (cw - 1.5) / 2, y + ch * 0.18, chip, ha="center", va="center",
             fontsize=8.6, color=col, zorder=3, fontweight="bold")

axB.text(50, 17.0,
         "The generator CAN tell whether the observation and the side channel agree —\n"
         "so it can tell which mirror pair it is in. It can NEVER tell which cell:\n"
         "honest and collude look identical to it, and so do poison and decouple.",
         ha="center", va="center", fontsize=9.1, color=INK, linespacing=1.55)
axB.text(50, 5.2,
         "That residual visibility is exactly the opening the adaptive cheater uses —\nwhich is why SHARPEN exists.",
         ha="center", va="center", fontsize=8.8, color=PURPLE, linespacing=1.5,
         style="italic")


# =====================================================================
# PANEL C — the metrics as cell contrasts
# =====================================================================
axC = fig.add_axes([0.525, 0.075, 0.44, 0.415])
axC.set_xlim(0, 100); axC.set_ylim(0, 100); axC.axis("off")
axC.text(0, 99, "C    every verdict metric is a contrast between those cells",
         fontsize=12.6, fontweight="bold", color=TITLE, ha="left", va="top")

rows = [
    ("lift",       "honest  −  baseline",         "Did the trace layer help at all?", NAVY),
    ("GROUND-GAP", "poison  −  decouple",         "Did it follow the OBSERVATION?\nBoth cells disagree, so only the\nobservation target differs.", GREEN),
    ("SHARPEN",    "(honest − collude) − GROUND-GAP",
     "Did it amplify when the side channel\nAGREED — beyond what grounding\nexplains? Paid for on collude.", ORANGE),
    ("OVERCONF",   "vs the honest reader's own value",
     "Was its confidence earned?\nSelf-referenced, because calibration\nis bounded away from 0 under blinding.", PURPLE),
]
y = 84
for name, formula, why, col in rows:
    axC.add_patch(Rectangle((1, y - 15.5), 97, 15.0, facecolor="white",
                            edgecolor=col, lw=1.5, zorder=2))
    axC.text(4, y - 3.4, name, fontsize=11.0, fontweight="bold", color=col,
             ha="left", va="center", zorder=3)
    axC.text(4, y - 8.6, formula, fontsize=9.3, color=INK, ha="left",
             va="center", zorder=3, family="DejaVu Sans")
    axC.text(45, y - 7.8, why, fontsize=8.2, color=MUTED, ha="left",
             va="center", zorder=3, linespacing=1.35)
    y -= 17.6

axC.text(50, 11.0,
         "Evaluated in that order, first match wins. A generator that clears every\n"
         "gate is inside the honest envelope — which is NOT a certificate of intent.",
         ha="center", va="center", fontsize=9.0, color=INK, linespacing=1.5)

fig.text(0.5, 0.030,
         "Read together: the substrate never sees the cause; the generator sees it only through an opacity-attenuated channel that, on 40% of trials, is pointed\n"
         "at a decoy instead; and the verdict is computed in a separate process the cause never enters. Every metric is a difference between two conditions\n"
         "the generator cannot tell apart.",
         ha="center", va="center", fontsize=9.6, color=MUTED, linespacing=1.5)

fig.savefig(OUT, dpi=170, facecolor="white", bbox_inches="tight")
print("wrote", OUT)
