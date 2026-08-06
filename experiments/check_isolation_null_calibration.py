#!/usr/bin/env python3
"""Read the isolated architecture arm as what it structurally is: a negative control.

Under context_isolated_score_only the judge prompt is byte-identical whether the
reference is correct or wrong (480/480 audited). So

    susceptibility = D(correct reference) - D(wrong reference)

has a TRUE value of exactly zero for every model, by construction. Anything the
estimator reports there is decoding noise. That makes the arm a direct read on
the false-positive rate of the paper's support rule:

    supported  <=>  n >= 12 complete items AND 95% item-clustered bootstrap
                    interval excludes zero

Any 'supported' call in this arm is a false positive.
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

ARCH = "context_isolated_score_only"

cell = defaultdict(dict)
items = set()
for line in open(OBS):
    r = json.loads(line)
    if r.get("error") is not None or r.get("score") is None:
        continue
    s = r["score"]
    cell[(r["model"], r["architecture"], r["item_id"], r["reference_variant"],
          r["candidate_type"])][r["repetition"]] = s
    items.add(r["item_id"])
ITEMS = sorted(items)


def complete(m, it, ref):
    return all(len(cell.get((m, ARCH, it, ref, c), {})) == 3
               for c in ("correct", "wrong_matching"))


def disc(m, it, ref):
    return (statistics.mean(cell[(m, ARCH, it, ref, "correct")].values())
            - statistics.mean(cell[(m, ARCH, it, ref, "wrong_matching")].values()))


print(f"negative control: {ARCH}")
print("true susceptibility is 0 for every row -- the prompt does not change\n")
print(f"{'model':<20} {'n':>3}  {'estimate':>9}  {'95% interval':>20}  call")
print("-" * 72)

per_item_all = []
supported = measurable = 0
for mid, name in MODELS:
    ok = [it for it in ITEMS
          if complete(mid, it, "correct_reference") and complete(mid, it, "wrong_reference")]
    vals = [disc(mid, it, "correct_reference") - disc(mid, it, "wrong_reference")
            for it in ok]
    n = len(vals)
    if n == 0:
        print(f"{name:<20} {n:>3}  {'--':>9}  {'--':>20}  no data")
        continue
    est = statistics.mean(vals)
    rng = random.Random(20260714)
    boots = sorted(statistics.mean(rng.choices(vals, k=n)) for _ in range(B))
    lo, hi = boots[int(.025 * B)], boots[int(.975 * B)]
    if n < FLOOR:
        call = "unmeasurable (below floor)"
    else:
        measurable += 1
        if lo > 0 or hi < 0:
            call = "*** SUPPORTED -- false positive ***"
            supported += 1
        else:
            call = "not supported (correct)"
        per_item_all += vals
    print(f"{name:<20} {n:>3}  {est:>+9.2f}  [{lo:>+8.2f}, {hi:>+8.2f}]  {call}")

print("-" * 72)
print(f"measurable arms: {measurable}   false positives: {supported} "
      f"({supported / measurable:.0%} at a nominal 5% rule)")

sd = statistics.pstdev(per_item_all)
print(f"\npooled per-item noise on a null contrast: sd = {sd:.2f} points, "
      f"n = {len(per_item_all)} items")
print(f"implied sd of a 16-item mean: {sd / 16 ** 0.5:.2f} points")
print(f"=> a null contrast on 16 items clears +/-{1.96 * sd / 16 ** 0.5:.1f} points "
      f"about 5% of the time on THIS estimator's assumptions,")
print("   but the arms above show it clearing more often than that in practice.")
