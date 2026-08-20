import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("v4_sweep.csv")
df["dprime_gap"] = df["planner_dprime"] - df["worker_dprime"]

COLORS = {0.0: "#1f4e79", 0.5: "#2e8b57", 1.0: "#b22222"}
QUALITIES = [0.0, 0.3, 0.6, 0.9]


def plot_policy(policy, filename, metric="planner_dprime", ylabel="Planner d'"):
    data = df[df["verify_policy"] == policy]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    # State the band's meaning on the figure itself: these images get lifted
    # out of the walkthrough and read on their own, and a shaded band is read
    # as a confidence interval unless it says otherwise.
    fig.suptitle(f"Verification policy: {policy}  —  {ylabel}\n"
                 f"lines = mean over 5 replicates; bands = ±1 SD across "
                 f"replicates (not confidence intervals)",
                 y=1.10, fontsize=13)

    for i, q in enumerate(QUALITIES):
        ax = axes[i]
        sub = data[data["poison_quality"] == q]

        for vr in [0.0, 0.5, 1.0]:
            # AGGREGATE OVER REPLICATES -- plotting raw rows draws a sawtooth
            g = (sub[sub["verify_rate"] == vr]
                 .groupby("poison_roots")[metric]
                 .agg(["mean", "std"])
                 .sort_index(ascending=False))
            ax.plot(g.index, g["mean"], marker="o", color=COLORS[vr],
                    label=f"verify_rate={vr}" if i == 3 else None)
            ax.fill_between(g.index, g["mean"] - g["std"], g["mean"] + g["std"],
                            color=COLORS[vr], alpha=0.15)

        # If plotting gap, draw a zero line
        if metric == "dprime_gap":
            ax.axhline(0, color="grey", ls="--", alpha=0.8,
                       label="Zero gain" if i == 3 else None)

        ax.set_title(f"poison_quality = {q}", fontsize=10)
        ax.set_xlim(10.5, 0.5)
        ax.set_xticks([10, 5, 2, 1])
        ax.set_xlabel("Hidden provenance roots M\n(fewer = more consolidated)")
        ax.grid(alpha=0.25)
        if i == 0:
            ax.set_ylabel(ylabel)
        if i == 3:
            ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", fontsize=8)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight", dpi=140)
    plt.close()


plot_policy("different", "different_dprime.png", "planner_dprime", "Planner d'")
plot_policy("different", "different_auroc.png", "planner_auroc", "Planner AUROC")
plot_policy("different", "different_dprime_gap.png", "dprime_gap",
            "d' Aggregation Gap (Planner - Worker)")
plot_policy("same", "same_dprime_gap.png", "dprime_gap",
            "d' Aggregation Gap (Planner - Worker)")
plot_policy("independent", "independent_dprime_gap.png", "dprime_gap",
            "d' Aggregation Gap (Planner - Worker)")
print("wrote 5 plots")

print("\n--- Silent Collapse Table ---")
# condition: different, quality 0.9, vr in [0.0, 0.5], comparing roots 10 and 1
sc_df = df[(df.verify_policy == "different") & (df.poison_quality == 0.9)
           & (df.verify_rate.isin([0.0, 0.5])) & (df.poison_roots.isin([10, 1]))]
sc_agg = sc_df.groupby(["verify_rate", "poison_roots"]).agg(
    Planner_D=("planner_D", "mean"),
    Planner_AUROC=("planner_auroc", "mean"),
    Commit_rate=("commit_rate", "mean"),
    Abstain_rate=("abstain_rate", "mean"),
    Mean_latency=("mean_latency", "mean")
).reset_index()

for vr in [0.0, 0.5]:
    v_data = sc_agg[sc_agg.verify_rate == vr].set_index("poison_roots")
    print(f"\nverify_rate = {vr}:")
    for metric in ["Planner_D", "Planner_AUROC", "Commit_rate",
                   "Abstain_rate", "Mean_latency"]:
        val10 = v_data.loc[10, metric]
        val1 = v_data.loc[1, metric]
        print(f"{metric}: 10 roots = {val10:.3f}, 1 root = {val1:.3f}, "
              f"delta = {val1 - val10:.3f}")
