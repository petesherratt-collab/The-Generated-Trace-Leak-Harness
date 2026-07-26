#!/usr/bin/env python3
"""Publication figures from leakharnessexperimentindex.xlsx.

Produces three figures that complement the five already built:
  Fig A  co-evolution ladder      (Versions sheet)
  Fig B  verdicts vs the draw     (Robustness sheet, 100 seeds)
  Fig C  detected vs neutralised  (Adversaries + Fork sheets)

House style matched to the existing figures: navy marks, crimson danger
zones on pink fill, green = accepted/passed, purple/orange = limits.
"""
import sys
import openpyxl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

XLSX = sys.argv[1] if len(sys.argv) > 1 else \
    "/root/.claude/uploads/0d07b602-a494-5c66-948a-5e890e6b9a57/b2a6b419-leakharnessexperimentindex.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/user/The-Generated-Trace-Leak-Harness/experiments"

# ---- house palette (read off the reference figures) -----------------------
NAVY      = "#1f3a5f"   # data marks, honest / known-honest
TITLE     = "#12345a"   # bold navy titles
INK       = "#333333"   # body text
MUTED     = "#6b7280"   # captions, secondary
GRID      = "#d9dde3"
CRIMSON   = "#b3122e"   # danger / fail / detected
PINKFILL  = "#fbe9e7"   # danger-zone fill
GREEN     = "#2c7a3f"   # accepted / passed / neutralised-safe
ORANGE    = "#e07b1a"   # sharpening
PURPLE    = "#6a3d9a"   # calibration / limit line
STEELMUT  = "#8fa2b7"   # faint marks

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.edgecolor": "#7a8494",
    "axes.linewidth": 1.0,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": "#5c6472",
    "ytick.color": "#5c6472",
    "figure.dpi": 130,
})

def load(sheet):
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    return list(wb[sheet].iter_rows(values_only=True))

def title_block(fig, title, subtitle, x=0.055, ytitle=0.955, ysub=0.912):
    fig.text(x, ytitle, title, ha="left", va="top", color=TITLE,
             fontsize=20, fontweight="bold")
    fig.text(x, ysub, subtitle, ha="left", va="top", color=MUTED, fontsize=12.5)

def caption(fig, text, y=0.045):
    fig.text(0.5, y, text, ha="center", va="center", color=MUTED,
             fontsize=10.6, wrap=True)


# ===========================================================================
# FIGURE A — the co-evolution ladder
# ===========================================================================
def fig_ladder():
    rows = load("Versions")
    header = None
    data = []
    for r in rows:
        if r and r[0] == "version":
            header = r
            continue
        if header and r and isinstance(r[0], str) and r[0].startswith("v0") or \
           (header and r and isinstance(r[0], str) and r[0].startswith("v1")):
            data.append(r)
    # columns: version, status, file, runs, verdict mode, attack, fix, metrics,
    #          weakness, rows in Results, PASS verdicts
    versions = [d[0] for d in data]
    attacks  = [d[5] for d in data]
    fixes    = [d[6] for d in data]
    status   = [d[1] for d in data]
    n = len(data)

    # short-form the attack that killed the previous version
    attack_short = [
        "substrate could be swapped underneath",
        "cause = label = trace-source conflated",
        "“observation” was a comment, not enforced",
        "public controls let a cheater impersonate honesty",
        "stateful base-rate learning (fixed cause)",
        "selection-bias collider (filter keyed on hidden T)",
        "“full-suite” laundering; a false header",
        "Omniscient Frame Thief — steals c and T from the stack",
        "objective rewarded uncalibrated amplification",
        "the verdict logic itself was unpinned",
    ]
    fix_short = [
        "vendored, hash-pinned substrate",
        "separate answer key; KEY-DECOUPLE",
        "real observation channel; OBS-DECOUPLE",
        "blind mirrored controls; GROUND-GAP + SHARPEN",
        "roam the cause per trial",
        "roam within E_d; no T-keyed filter",
        "domain accounting; inertness proof; exchangeability measured",
        "process isolation (fresh --worker)",
        "signed-overconfidence CALIBRATION gate",
        "full-file hash pin; self-verifying, HMAC'd worker",
    ]

    fig = plt.figure(figsize=(13.6, 10.4))
    title_block(fig,
                "Ten rounds, each closing the flaw that killed the round before",
                "Every version was broken by a reviewer who found the one load-bearing hole — the next closed exactly that hole, in code.",
                ytitle=0.972, ysub=0.935)
    ax = fig.add_axes([0.055, 0.065, 0.90, 0.80])
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.65, n - 0.35)
    ax.invert_yaxis()
    ax.axis("off")

    x_ver, x_attack, x_fix = 0.30, 1.55, 5.55
    # column headers (fig-level so they sit clear of the subtitle)
    fig.text(0.055 + 0.90 * x_ver / 10, 0.895, "version", color=MUTED,
             fontsize=11, fontweight="bold", ha="center")
    fig.text(0.055 + 0.90 * x_attack / 10, 0.895, "the attack that killed the previous version",
             color=CRIMSON, fontsize=11.5, fontweight="bold", ha="left")
    fig.text(0.055 + 0.90 * x_fix / 10, 0.895, "the fix this version introduced",
             color=GREEN, fontsize=11.5, fontweight="bold", ha="left")

    for i in range(n):
        y = i
        # connector rung
        if i < n - 1:
            ax.plot([x_ver, x_ver], [y + 0.18, y + 0.82], color=GRID, lw=2.2, zorder=1)
        canon = "CANONICAL" in str(status[i])
        # version node
        ax.scatter([x_ver], [y], s=680 if canon else 560,
                   color=GREEN if canon else NAVY, zorder=3,
                   edgecolor="white", linewidth=1.6)
        ax.text(x_ver, y, versions[i], color="white",
                fontsize=10 if canon else 9.2, fontweight="bold",
                ha="center", va="center", zorder=4)
        # attack (crimson) — arrives INTO this version
        ax.text(x_attack, y, "✖  " + attack_short[i], color=CRIMSON,
                fontsize=11.0, ha="left", va="center")
        # fix (green)
        ax.text(x_fix, y, "→  " + fix_short[i], color=INK,
                fontsize=11.0, ha="left", va="center")
        if canon:
            ax.text(x_ver + 0.42, y, "canonical", color=GREEN, fontsize=10,
                    fontweight="bold", ha="left", va="center", style="italic")

    caption(fig,
            "Each retired attacker still lives in the canonical file as a runnable class, so any regression re-appears as a failing run. "
            "The substrate block stayed byte-identical across all ten versions — its hash is the same from v0.6 to v1.5.",
            y=0.038)
    out = f"{OUT}/figA_coevolution_ladder.png"
    fig.savefig(out, dpi=170, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return out


# ===========================================================================
# FIGURE B — which verdicts depend on the random draw
# ===========================================================================
def fig_robustness():
    rows = load("Robustness")
    data = []
    for r in rows:
        if r and r[0] in list("ABCDEFGH"):
            data.append(r)
    # cols: run, class, mode, modal verdict, seeds agreeing, stability, other, ...
    recs = []
    for r in rows:
        if r and r[0] in list("ABCDEFGH"):
            run, cls, mode, modal, seeds, stab, other = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
            recs.append(dict(run=run, cls=cls, mode=mode, modal=modal,
                             seeds=int(seeds), stab=stab, other=other))

    # keep the ISOLATED mode (the line that counts as the verdict)
    iso = [d for d in recs if d["mode"] == "ISOLATED"]
    order = list("ABCDEFGH")
    iso.sort(key=lambda d: order.index(d["run"]))

    verdict_color = {
        "NO LIFT": STEELMUT,
        "PASS": GREEN,
        "SUSPECT (localisation leak)": CRIMSON,
        "SUSPECT (confidence-sharpening)": ORANGE,
        "SUSPECT (calibration)": PURPLE,
    }
    labels = [f"{d['run']}  ·  {d['cls']}" for d in iso]
    seeds = [d["seeds"] for d in iso]

    # Plot the FLIPS (seeds disagreeing), not the agreement count: a bar must
    # start at zero, and 98-vs-100 on a truncated axis would exaggerate a 2% gap.
    flips = [100 - d["seeds"] for d in iso]

    fig = plt.figure(figsize=(14.0, 9.0))
    title_block(fig,
                "Which verdicts hold on every draw — and which wobble",
                "Every isolated verdict was recomputed on 100 random seeds. The bar is how many of those 100 seeds returned a DIFFERENT verdict.",
                ytitle=0.968, ysub=0.928)
    ax = fig.add_axes([0.275, 0.235, 0.60, 0.60])
    y = list(range(len(iso)))[::-1]

    for yi, d, f in zip(y, iso, flips):
        c = verdict_color.get(d["modal"], NAVY)
        if f == 0:
            ax.text(0.035, yi, "stable on all 100 seeds", color=MUTED,
                    fontsize=10, va="center", ha="left", style="italic")
        else:
            ax.barh(yi, f, height=0.60, color=c, zorder=3,
                    edgecolor="white", linewidth=1.2)
            seedword = "seed" if f == 1 else "seeds"
            ax.text(f + 0.045, yi, f"{f} {seedword} of 100 flipped to SUSPECT (confidence-sharpening)",
                    color=CRIMSON if d["run"] == "B" else INK,
                    fontsize=10, va="center", ha="left",
                    fontweight="bold" if d["run"] == "B" else "normal")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.6)
    ax.set_xlim(0, 2.9)
    ax.set_xticks([0, 1, 2])
    ax.set_xlabel("seeds (of 100) that returned a different verdict", fontsize=11.5,
                  color=INK, labelpad=8)
    ax.grid(axis="x", color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    # call out the one that is an actual false accusation
    yB = [yi for yi, d in zip(y, iso) if d["run"] == "B"][0]
    ax.annotate("B is the positive control — a generator we KNOW is honest.\n"
                "Every seed that flips it is the harness accusing an innocent.",
                xy=(1.0, yB - 0.32), xytext=(1.34, yB - 1.30),
                fontsize=9.6, color=CRIMSON, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=CRIMSON, lw=1.6),
                bbox=dict(boxstyle="round,pad=0.45", fc=PINKFILL, ec=CRIMSON, lw=1.2))

    # verdict legend
    seen = []
    for d in iso:
        if d["modal"] not in seen:
            seen.append(d["modal"])
    handles = [plt.Line2D([0], [0], marker="s", ls="", ms=11,
                          markerfacecolor=verdict_color.get(v, NAVY),
                          markeredgecolor="white") for v in seen]
    fig.legend(handles, seen,
               loc="lower center", bbox_to_anchor=(0.5, 0.015), ncol=5,
               frameon=False, fontsize=9.6, handletextpad=0.4, columnspacing=1.4,
               title="the usual verdict each bar belongs to", title_fontsize=9.6)

    caption(fig,
            "Seven of the sixteen run×mode verdicts flip on at least one seed, and every flip lands on the same gate: confidence-sharpening. Its honest-reader null sits just 2.2σ\n"
            "from a hand-set 0.02 cutoff, so it occasionally accuses the innocent control and — being evaluated before calibration — steals the stated reason from runs F, G and H.\n"
            "The other gates clear their cutoffs by 6–8σ. The wobble is small, but it is the empirical case for deriving these thresholds instead of stipulating them.",
            y=0.105)
    out = f"{OUT}/figB_verdicts_vs_draw.png"
    fig.savefig(out, dpi=170, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return out


# ===========================================================================
# FIGURE C — detected vs merely neutralised
# ===========================================================================
def fig_detected_neutralised():
    rows = load("Adversaries")
    recs = []
    for r in rows:
        if r and r[0] in list("ABCDEFGH"):
            recs.append(dict(run=r[0], cls=r[1], first=r[2], exploits=r[3],
                             gate=r[4], verdict=r[5], outcome=r[6], why=r[7]))

    # classify outcome into a column bucket
    def bucket(o):
        o = str(o)
        if o.startswith("n/a"):
            return "control"
        if "NEUTRALISED, not detected" in o:
            return "neutralised"
        if "NEUTRALISED then DETECTED" in o or o.startswith("DETECTED"):
            return "detected"
        return "detected"

    cols = ["control", "detected", "neutralised"]
    col_x = {"control": 1.6, "detected": 5.0, "neutralised": 8.6}
    col_title = {
        "control": ("CONTROLS", "define the floor and the ceiling", NAVY),
        "detected": ("DETECTED", "a gate actively fires and names the cheat", CRIMSON),
        "neutralised": ("NEUTRALISED, not detected", "isolation removes the tool; the harness never sees the attacker", ORANGE),
    }
    buckets = {c: [] for c in cols}
    for d in recs:
        buckets[bucket(d["outcome"])].append(d)

    fig = plt.figure(figsize=(14.4, 9.6))
    title_block(fig,
                "Caught, or just disarmed? The distinction the whole project turns on",
                "Eight generators, sorted by what actually happened to them. A fix that only removes an attacker's tool is never recorded as a detection.",
                ytitle=0.970, ysub=0.930)
    ax = fig.add_axes([0.02, 0.135, 0.96, 0.735])
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 10)
    ax.invert_yaxis()
    ax.axis("off")

    vcol = {
        "NO LIFT": STEELMUT, "PASS": GREEN,
        "SUSPECT (localisation leak)": CRIMSON,
        "SUSPECT (confidence-sharpening)": ORANGE,
        "SUSPECT (calibration)": PURPLE,
    }

    # column separators / headers
    for c in cols:
        x = col_x[c]
        t, sub, col = col_title[c]
        ax.text(x, 0.05, t, color=col, fontsize=13, fontweight="bold", ha="center")
        ax.text(x, 0.62, sub, color=MUTED, fontsize=9.4, ha="center", style="italic")
    for xdiv in (3.3, 6.8):
        ax.axvline(xdiv, color=GRID, lw=1.3, ymin=0.06, ymax=0.97)

    # card layout within each column
    row_h = 1.72
    y0 = 1.45
    for c in cols:
        x = col_x[c]
        for j2, d in enumerate(buckets[c]):
            y = y0 + j2 * row_h
            card_col = vcol.get(d["verdict"], NAVY)
            box = FancyBboxPatch((x - 1.45, y - 0.55), 2.9, 1.28,
                                 boxstyle="round,pad=0.02,rounding_size=0.10",
                                 linewidth=1.4, edgecolor=card_col,
                                 facecolor="white", zorder=2)
            ax.add_patch(box)
            ax.scatter([x - 1.16], [y - 0.18], s=290, color=card_col, zorder=3,
                       edgecolor="white", linewidth=1.2)
            ax.text(x - 1.16, y - 0.18, d["run"], color="white", fontsize=9.8,
                    fontweight="bold", ha="center", va="center", zorder=4)
            name = d["cls"].split(" -> ")[0]
            ax.text(x - 0.88, y - 0.18, name, color=TITLE, fontsize=10.0,
                    fontweight="bold", ha="left", va="center")
            ax.text(x - 1.30, y + 0.24, d["verdict"], color=card_col,
                    fontsize=9.4, ha="left", va="center", fontweight="bold")
            expl = str(d["exploits"])
            if len(expl) > 50:
                expl = expl[:48] + "…"
            ax.text(x - 1.30, y + 0.55, expl, color=MUTED, fontsize=7.7,
                    ha="left", va="center")

    # locate E and H for the two "tells"
    yE = yH = None
    for j2, d in enumerate(buckets["neutralised"]):
        if d["run"] == "E":
            yE = y0 + j2 * row_h
    for j2, d in enumerate(buckets["detected"]):
        if d["run"] == "H":
            yH = y0 + j2 * row_h

    # RUN E tell — sits in the empty space under the neutralised column
    if yE is not None:
        ax.annotate("RUN E — the tell for IMPOSSIBILITY\n"
                    "The harness never catches it. Isolated, it PASSes:\n"
                    "the attacker's tool is gone, but the attacker was\n"
                    "never seen. That is the shape of a negative result.",
                    xy=(col_x["neutralised"], yE + 0.78),
                    xytext=(col_x["neutralised"], yE + 2.35),
                    fontsize=9.4, color=CRIMSON, ha="center", va="center",
                    arrowprops=dict(arrowstyle="->", color=CRIMSON, lw=1.7),
                    bbox=dict(boxstyle="round,pad=0.5", fc=PINKFILL, ec=CRIMSON, lw=1.3))

    # RUN H tell — to the right of the detected column, in the gap
    if yH is not None:
        ax.annotate("RUN H — the tell for INSTRUMENT\n"
                    "Isolation and calibration are each necessary\n"
                    "and only jointly sufficient. Two orthogonal\n"
                    "constraints DID catch an omniscient thief.",
                    xy=(col_x["neutralised"] - 1.62, yH),
                    xytext=(col_x["neutralised"] + 0.15, yH - 0.15),
                    fontsize=9.4, color=GREEN, ha="center", va="center",
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.7),
                    bbox=dict(boxstyle="round,pad=0.5", fc="#edf6ef", ec=GREEN, lw=1.3))

    caption(fig,
            "The strategic fork the project has not resolved. RUN H is evidence the harness is a shippable instrument; RUN E is evidence it is instead an impossibility result —\n"
            "that honest and a perfectly-disarmed leaker cannot be told apart from behaviour alone. Deciding between them sets the stopping condition for every future round.",
            y=0.055)
    out = f"{OUT}/figC_detected_vs_neutralised.png"
    fig.savefig(out, dpi=170, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return out


if __name__ == "__main__":
    a = fig_ladder()
    b = fig_robustness()
    c = fig_detected_neutralised()
    print("wrote:")
    for p in (a, b, c):
        print(" ", p)
