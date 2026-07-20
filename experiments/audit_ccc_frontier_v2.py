"""Independent audit of the CCC frontier v2 run.

Re-implemented from scratch (does NOT import run_ccc_frontier.analyse) so the contrast
recomputation is a genuine cross-check. Reads only the raw JSONL rows.
"""
import json, os, collections, random, statistics

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
REPS = 3
CONDS = ["no_injection", "answer_only", "full_rationale", "solver_rationale"]
CANDS = ["correct", "wrong_matching"]
FLOOR = {"arith": 12, "code": 12, "sql": 18}   # 75% of 16/16/24
DOMAINS = ["arith", "code", "sql"]


def rows(domain):
    p = os.path.join(RES, f"ccc_frontier_v2_{domain}_obs.jsonl")
    return [json.loads(l) for l in open(p) if l.strip()]


def is_success(r):
    return r.get("score") is not None and r.get("error") is None


def ckey(r):
    return (r["item_id"], r["model"], r["condition"], r["candidate_type"], r["repetition"])


def disc(obs, model, cond, ids):
    """Per-item discrimination = mean_reps s(correct) - mean_reps s(wrong), when complete."""
    out = {}
    for iid in ids:
        cor = [obs.get((iid, model, cond, "correct", rp)) for rp in range(REPS)]
        wro = [obs.get((iid, model, cond, "wrong_matching", rp)) for rp in range(REPS)]
        if all(x is not None for x in cor) and all(x is not None for x in wro):
            out[iid] = statistics.mean(cor) - statistics.mean(wro)
    return out


def boot(per, n=6000, seed=0):
    it = list(per)
    if not it:
        return float("nan"), float("nan"), float("nan"), 0
    r = random.Random(seed)
    ms = sorted(sum(per[r.choice(it)] for _ in it) / len(it) for _ in range(n))
    return statistics.mean(per.values()), ms[int(.025 * n)], ms[int(.975 * n)], len(it)


print("=" * 78)
print("CCC FRONTIER v2 — INDEPENDENT AUDIT")
print("=" * 78)

for domain in DOMAINS:
    rs = rows(domain)
    models = sorted({r["model"] for r in rs})
    ids = sorted({r["item_id"] for r in rs})
    floor = FLOOR[domain]

    # ---- [1] structural integrity ----
    succ = [r for r in rs if is_success(r)]
    dup = collections.Counter(ckey(r) for r in succ)
    dups = {k: c for k, c in dup.items() if c > 1}
    has_attempts = sum(1 for r in rs if "attempts" in r)
    print(f"\n### {domain}  ({len(ids)} items, floor {floor}) — {len(rs)} rows, "
          f"{len(succ)} success, {len(rs)-len(succ)} missing")
    print(f"  [struct] duplicate successful cells: {len(dups)}   "
          f"rows with attempts field: {has_attempts}/{len(rs)}")
    # expected cells per model = items*conds*cands*reps
    exp = len(ids) * len(CONDS) * len(CANDS) * REPS
    per_model_rows = collections.Counter(r["model"] for r in rs)
    print(f"  [struct] expected rows/model={exp}; actual: "
          + ", ".join(f"{m.split('/')[-1]}={per_model_rows[m]}" for m in models))

    # ---- [2] condition-balanced missingness per (model x condition) ----
    print("  [missingness by model x condition]  (fail counts; * = concentrated in injection)")
    for m in models:
        line = []
        fails_by_cond = {}
        for c in CONDS:
            tot = sum(1 for r in rs if r["model"] == m and r["condition"] == c)
            fail = sum(1 for r in rs if r["model"] == m and r["condition"] == c and not is_success(r))
            fails_by_cond[c] = fail
            line.append(f"{c.split('_')[0][:4]}:{fail}/{tot}")
        base_fail = fails_by_cond["no_injection"]
        inj_fail = sum(fails_by_cond[c] for c in CONDS if c != "no_injection")
        flag = " *INJECTION-SKEWED" if inj_fail > 3 * max(base_fail, 1) and inj_fail > 6 else ""
        print(f"     {m:34s} " + "  ".join(line) + flag)

    # ---- [3] finish_reason diagnosis on failures (esp. truncation) ----
    print("  [finish_reason on FAILED cells, by model]")
    for m in models:
        fr = collections.Counter()
        for r in rs:
            if r["model"] == m and not is_success(r):
                # prefer per-attempt finish reasons for the full picture
                ats = r.get("attempts") or []
                if ats:
                    fr[tuple(a.get("finish_reason") for a in ats)] += 1
                else:
                    fr[(r.get("finish_reason"),)] += 1
        if fr:
            desc = ", ".join(f"{list(k)}×{v}" for k, v in fr.most_common(4))
            print(f"     {m:34s} {desc}")

    # ---- [4] independent contrast recomputation ----
    obs = {ckey(r): r["score"] for r in succ}
    print("  [recomputed contrasts]  bare-harm = D(no_injection) - D(answer_only)")
    print(f"     {'model':34s} {'bare-harm [95% CI]':>26s}  n   verdict     prov+   rat+")
    for m in models:
        base = disc(obs, m, "no_injection", ids)
        bare = disc(obs, m, "answer_only", ids)
        full = disc(obs, m, "full_rationale", ids)
        solv = disc(obs, m, "solver_rationale", ids)
        harm = {i: base[i] - bare[i] for i in set(base) & set(bare)}
        mn, lo, hi, n = boot(harm)
        prov = {i: full[i] - solv[i] for i in set(solv) & set(full)}
        rat = {i: bare[i] - full[i] for i in set(full) & set(bare)}
        pm = statistics.mean(prov.values()) if prov else float("nan")
        rm = statistics.mean(rat.values()) if rat else float("nan")
        verdict = "SUPPORTED" if (n >= floor and lo > 0) else ("unmeasurable" if n < floor else "ns")
        print(f"     {m:34s} {mn:+7.2f} [{lo:+7.2f},{hi:+7.2f}] {n:2d}  {verdict:12s} "
              f"{pm:+6.1f} {rm:+6.1f}")

print("\n" + "=" * 78)
print("done")
