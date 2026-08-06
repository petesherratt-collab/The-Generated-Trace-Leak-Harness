#!/usr/bin/env python3
"""Is a wrong reference worse than no reference at all?

Paired, item-clustered bootstrap on

    D(contaminated, wrong reference) - D(isolated)

for items complete in BOTH arms. Same estimator, floor and B as every other
figure in the paper. No interpretation -- just whether the difference is
supported in the preregistered sense.
"""
import json, random, statistics, sys
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OBS = f"{ROOT}/experiments/results/architecture_obs.jsonl"
B, FLOOR = 4000, 12

MODELS = [("openai/gpt-4o-mini", "GPT-4o mini"),
          ("anthropic/claude-haiku-4.5", "Claude Haiku 4.5"),
          ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
          ("deepseek/deepseek-chat", "DeepSeek Chat"),
          ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B")]

ISO, CON = "context_isolated_score_only", "contaminated_score_only"

cell = defaultdict(dict)
items = set()
for line in open(OBS):
    r = json.loads(line)
    if r.get("error") is not None or r.get("score") is None:
        continue
    cell[(r["model"], r["architecture"], r["item_id"],
          r["reference_variant"], r["candidate_type"])][r["repetition"]] = r["score"]
    items.add(r["item_id"])
ITEMS = sorted(items)


def complete(m, a, it, ref):
    return all(len(cell.get((m, a, it, ref, c), {})) == 3
               for c in ("correct", "wrong_matching"))


def disc(m, a, it, ref):
    return (statistics.mean(cell[(m, a, it, ref, "correct")].values())
            - statistics.mean(cell[(m, a, it, ref, "wrong_matching")].values()))


def boot(vals, seed):
    n = len(vals)
    rng = random.Random(seed)
    b = sorted(statistics.mean(rng.choices(vals, k=n)) for _ in range(B))
    return b[int(.025 * B)], b[int(.975 * B)]


print("D(wrong reference) - D(no reference), paired within item\n")
print(f"{'model':<20} {'n':>3}  {'difference':>10}  {'95% interval':>20}  supported?")
print("-" * 74)

for mid, name in MODELS:
    ok = [it for it in ITEMS
          if complete(mid, CON, it, "wrong_reference") and complete(mid, ISO, it, "wrong_reference")]
    vals = [disc(mid, CON, it, "wrong_reference") - disc(mid, ISO, it, "wrong_reference")
            for it in ok]
    n = len(vals)
    if n == 0:
        print(f"{name:<20} {n:>3}  {'--':>10}")
        continue
    est = statistics.mean(vals)
    lo, hi = boot(vals, 20260714)
    if n < FLOOR:
        call = "unmeasurable (below floor)"
    elif hi < 0:
        call = "YES - worse than no reference"
    elif lo > 0:
        call = "yes - better than no reference"
    else:
        call = "no - interval covers zero"
    print(f"{name:<20} {n:>3}  {est:>+10.2f}  [{lo:>+8.2f}, {hi:>+8.2f}]  {call}")

print("\n\nAnd the mirror: D(correct reference) - D(no reference)\n")
print(f"{'model':<20} {'n':>3}  {'difference':>10}  {'95% interval':>20}")
print("-" * 62)
for mid, name in MODELS:
    ok = [it for it in ITEMS
          if complete(mid, CON, it, "correct_reference") and complete(mid, ISO, it, "wrong_reference")]
    vals = [disc(mid, CON, it, "correct_reference") - disc(mid, ISO, it, "wrong_reference")
            for it in ok]
    n = len(vals)
    if n == 0:
        continue
    est = statistics.mean(vals)
    lo, hi = boot(vals, 20260714)
    flag = "" if n >= FLOOR else "  (below floor)"
    print(f"{name:<20} {n:>3}  {est:>+10.2f}  [{lo:>+8.2f}, {hi:>+8.2f}]{flag}")
