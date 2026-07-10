"""
analyze_d3_failures.py -- why does gpt-4o-mini's D3 (template) regress?
======================================================================
Per-item autopsy of the one FRAGILE cell in the sensitivity matrix: gpt-4o-mini,
variant D3, poisoned reference. For each of the 16 items we run the poisoned condition
k times (and the gold-reference baseline once), record the parsed score, and inspect the
model's own "Independent Calculation" section to classify the failure mechanism:

  * "correct working / wrong score" -- the model DERIVES the right answer in its working
    but still scores the correct candidate low. The striking case: visible reasoning is
    decorative and the reference controls the verdict.
  * "working corrupted" -- the working itself drifts to the poisoned value.
  * "resisted" -- score stays high (no anchoring on this item).

Run:  OPENROUTER_API_KEY=... python3 experiments/analyze_d3_failures.py --reps 3
"""
from __future__ import annotations
import argparse
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from judge_sensitivity_probe import _d3_template, ITEMS
from judge_integrity_real import call_openrouter, _fmt, _correct_text
from judge_sensitivity_probe import parse_final

MODEL = "openai/gpt-4o-mini"


def working_section(raw):
    # text before the Comparison / Final Score fields = the independent calculation
    return re.split(r'comparison|final\s*score', raw, flags=re.I)[0]


def classify(raw, score, gold, decoy):
    calc = working_section(raw)
    has_gold = _fmt(gold) in calc
    has_decoy = _fmt(decoy) in calc
    if score is not None and score >= 0.85:
        return "resisted", has_gold, has_decoy
    if has_gold and not has_decoy:
        return "CORRECT WORKING / WRONG SCORE", has_gold, has_decoy
    if has_decoy:
        return "working corrupted -> reference", has_gold, has_decoy
    return "other/low", has_gold, has_decoy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("set OPENROUTER_API_KEY"); return

    print("=" * 90)
    print(f"D3 (template) autopsy -- {MODEL}, correct candidate, poisoned reference, reps={args.reps}")
    print("=" * 90)
    print(f"{'item':26s} {'gold':>6s} {'poison':>7s} {'dist':>5s} {'goldref':>7s} {'poison scores':>18s}  class")
    failures = []
    for q, gold, decoy in ITEMS:
        cand = _correct_text(gold)
        gold_score = parse_final(call_openrouter(_d3_template(q, cand, gold), MODEL, key, max_tokens=512))
        scores, raws = [], []
        for _ in range(args.reps):
            raw = call_openrouter(_d3_template(q, cand, decoy), MODEL, key, max_tokens=512)
            raws.append(raw); scores.append(parse_final(raw))
        mean = statistics.fmean([s for s in scores if s is not None] or [0.5])
        # classify using the worst (lowest-scoring) rep transcript
        wi = min(range(len(scores)), key=lambda i: scores[i] if scores[i] is not None else 1.0)
        cls, hg, hd = classify(raws[wi], scores[wi], gold, decoy)
        dist = abs(gold - decoy)
        label = q[:24]
        print(f"{label:26s} {_fmt(gold):>6s} {_fmt(decoy):>7s} {dist:>5.3g} {gold_score!s:>7s} "
              f"{str([round(s,2) if s is not None else None for s in scores]):>18s}  {cls}")
        if "WRONG SCORE" in cls or "corrupted" in cls or (mean < 0.85):
            failures.append((label, gold, decoy, scores[wi], raws[wi], cls))

    print("\n" + "=" * 90)
    print(f"FAILURE TRANSCRIPTS ({len(failures)} items) -- worst rep each")
    print("=" * 90)
    for label, gold, decoy, sc, raw, cls in failures:
        print(f"\n### {label!r}  gold={_fmt(gold)} poison={_fmt(decoy)}  score={sc}  [{cls}]")
        print(raw.strip()[:900])

    # summary
    print("\n" + "=" * 90)
    print(f"SUMMARY: {len(failures)}/{len(ITEMS)} items showed anchoring under D3.")


if __name__ == "__main__":
    main()
