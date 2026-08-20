"""
Emits every number quoted in walkthrough.md, so the write-up is auditable
against the sweep rather than eyeballed off the charts.

Run after v4_simulation.py has produced v4_sweep.csv.
"""

import pandas as pd

df = pd.read_csv("v4_sweep.csv")
pd.set_option("display.width", 200)


def rule(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


# ---------------------------------------------------------------------------
rule("CRN identity test: poison_roots=10 must reproduce the matched baseline")
ident = df[df.poison_roots == 10]
print("max |planner_D delta| :", ident.planner_D_delta.abs().max())
print("max |commit delta|    :", ident.commit_rate_delta.abs().max())

rule("d' vs AUROC agreement (planner), Spearman")
sub = df[["planner_dprime", "planner_auroc"]].dropna()
print(round(sub.corr(method="spearman").iloc[0, 1], 4))

# ---------------------------------------------------------------------------
rule("Worker d' by (quality, roots) -- flat across roots, degraded by quality")
print(df.groupby(["poison_quality", "poison_roots"])["worker_dprime"]
        .mean().round(3).unstack().to_string())

# ---------------------------------------------------------------------------
rule("walkthrough S1 gap table: roots=1, verify_rate=0")
g = df[(df.poison_roots == 1) & (df.verify_rate == 0.0)]
gap = (g.groupby("poison_quality")[["worker_dprime", "planner_dprime"]]
         .mean()
         .assign(gain=lambda d: d.planner_dprime - d.worker_dprime)
         .round(3))
print(gap.to_string())

# ---------------------------------------------------------------------------
rule("walkthrough S1 silent-collapse table: policy=different, quality=0.9")
sc = df[(df.verify_policy == "different") & (df.poison_quality == 0.9)
        & (df.poison_roots.isin([10, 1]))]
sc_agg = sc.groupby(["verify_rate", "poison_roots"]).agg(
    planner_D=("planner_D", "mean"),
    planner_auroc=("planner_auroc", "mean"),
    commit_rate=("commit_rate", "mean"),
    abstain_rate=("abstain_rate", "mean"),
    mean_latency=("mean_latency", "mean"),
)
print(sc_agg.round(3).to_string())
for vr in [0.0, 0.5]:
    v = sc_agg.loc[vr]
    print(f"\ndeltas at verify_rate={vr} (1 root minus 10 roots):")
    # difference the unrounded means, then round -- differencing pre-rounded
    # values disagrees with plot_v4.py in the third decimal
    print((v.loc[1] - v.loc[10]).round(3).to_string())

# ---------------------------------------------------------------------------
rule("walkthrough S1 policy table: quality=0.6, roots=1, verify_rate=1.0")
ref = df[(df.poison_quality == 0.6) & (df.poison_roots == 10)
         & (df.verify_rate == 0.0)]["planner_D"].mean()
none = df[(df.poison_quality == 0.6) & (df.poison_roots == 1)
          & (df.verify_rate == 0.0)]["planner_D"].mean()
gap_total = ref - none
print(f"M=10 unverified reference : {ref:.3f}")
print(f"roots=1 unverified ('none'): {none:.3f}")
print(f"gap to close              : {gap_total:.3f}\n")

rows = [("none", none)]
for pol in ["same", "different", "independent"]:
    v = df[(df.poison_quality == 0.6) & (df.poison_roots == 1)
           & (df.verify_rate == 1.0) & (df.verify_policy == pol)]["planner_D"].mean()
    rows.append((pol, v))
for name, v in rows:
    share = "" if name == "none" else f"{(v - none) / gap_total * 100:5.1f}%"
    print(f"{name:<13} planner_D={v:.3f}  share of gap closed={share}")

# ---------------------------------------------------------------------------
rule("Selective disablement: accept-rate decomposition by class\n"
     "(quality=0.6, roots=1, verify_rate=1.0)\n"
     "At roots=1 every poisoned apparent source shares the one root, so on\n"
     "POISONED tasks 'different' is mathematically identical to 'same'.\n"
     "Any advantage 'different' shows must therefore come from GENUINE tasks.")
dec = df[(df.poison_quality == 0.6) & (df.poison_roots == 1)
         & (df.verify_rate == 1.0)]
dec_agg = dec.groupby("verify_policy")[
    ["worker_p_accept_true", "worker_p_accept_false",
     "planner_p_accept_true", "planner_p_accept_false", "planner_D"]
].mean().round(4)
print(dec_agg.to_string())

same = dec_agg.loc["same"]
diff = dec_agg.loc["different"]
print("\ndifferent minus same:")
print(f"  planner_p_accept_true  (genuine tasks) : {diff.planner_p_accept_true - same.planner_p_accept_true:+.4f}")
print(f"  planner_p_accept_false (poisoned tasks): {diff.planner_p_accept_false - same.planner_p_accept_false:+.4f}")
print(f"  planner_D                              : {diff.planner_D - same.planner_D:+.4f}")

# same decomposition across all roots, to show the false-class term only
# collapses to zero as M -> 1
print("\n'different' minus 'same' by roots (quality=0.6, verify_rate=1.0):")
byroot = df[(df.poison_quality == 0.6) & (df.verify_rate == 1.0)
            & (df.verify_policy.isin(["same", "different"]))]
piv = byroot.pivot_table(index="poison_roots", columns="verify_policy",
                         values=["planner_p_accept_true", "planner_p_accept_false"],
                         aggfunc="mean")
out = pd.DataFrame({
    "d_accept_true": piv[("planner_p_accept_true", "different")]
                     - piv[("planner_p_accept_true", "same")],
    "d_accept_false": piv[("planner_p_accept_false", "different")]
                      - piv[("planner_p_accept_false", "same")],
}).round(4).sort_index(ascending=False)
print(out.to_string())

# ---------------------------------------------------------------------------
rule("Comparator check for 'independent': which reference?\n"
     "planner_D at quality=0.6 for roots in {1,10} x verify_rate in {0,1}")
comp = df[(df.poison_quality == 0.6) & (df.poison_roots.isin([1, 10]))
          & (df.verify_rate.isin([0.0, 1.0]))]
print(comp.pivot_table(index=["poison_roots", "verify_rate"],
                       columns="verify_policy", values="planner_D",
                       aggfunc="mean").round(3).to_string())
ind_1 = df[(df.poison_quality == 0.6) & (df.poison_roots == 1)
           & (df.verify_rate == 1.0) & (df.verify_policy == "independent")]["planner_D"].mean()
ind_10 = df[(df.poison_quality == 0.6) & (df.poison_roots == 10)
            & (df.verify_rate == 1.0) & (df.verify_policy == "independent")]["planner_D"].mean()
print(f"\nvs UNVERIFIED M=10 reference ({ref:.3f}): "
      f"{(ind_1 - none) / gap_total * 100:.1f}% of gap closed -- exceeds 100%,")
print("  because the idealised policy also lifts the M=10 reference itself.")
print(f"vs LIKE-FOR-LIKE verified M=10 reference ({ind_10:.3f}): "
      f"{(ind_1 - none) / (ind_10 - none) * 100:.1f}% of gap closed.")
