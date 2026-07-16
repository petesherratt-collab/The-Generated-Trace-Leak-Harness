"""monitor_ccc_stage1.py -- check on a Stage-1 code-domain run at any time.

Reads the streamed evidence (results/ccc_code_obs_stage1.jsonl) WITHOUT touching
the run, and prints where things are: completion, successes/failures, throughput,
ETA, and a per-model / per-protocol breakdown. Safe to run from a second terminal
while the run is going -- it only reads.

  python3 experiments/monitor_ccc_stage1.py            # one snapshot
  python3 experiments/monitor_ccc_stage1.py --watch 600  # refresh every 10 min

The run's own heartbeat (run_ccc_codedomain.py --progress-secs) writes the same kind
of line to results/ccc_code_progress_stage1.txt; this monitor is the on-demand view.
"""
from __future__ import annotations

import argparse
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OBS = os.path.join(RES, "ccc_code_obs_stage1.jsonl")

MODELS = [
    "openai/gpt-4o-mini", "anthropic/claude-haiku-4.5", "google/gemini-2.5-flash",
    "deepseek/deepseek-chat", "meta-llama/llama-3.3-70b-instruct",
]
TOTAL = 3840
PER_MODEL = TOTAL // len(MODELS)      # 768
PROTOCOLS = ("score_only", "verify_written")


def snapshot(path=OBS):
    if not os.path.exists(path):
        print(f"no evidence yet at {os.path.relpath(path)} -- run not started (or wrong cwd).")
        return
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    # one final state per cell (dedup key); a later success supersedes an earlier failure
    from collections import defaultdict
    cell = {}
    for r in rows:
        k = (r["item_id"], r["model"], r["label"], r["content"],
             r["candidate_type"], r["repetition"], r["protocol"])
        ok = r.get("score") is not None and r.get("error") is None
        if k not in cell or ok:               # prefer a success
            cell[k] = ok
    done = len(cell)
    ok = sum(1 for v in cell.values() if v)
    fail = done - ok
    ts = [r["timestamp"] for r in rows if "timestamp" in r]
    span = (max(ts) - min(ts)) if len(ts) > 1 else 0.0
    rate = done / span * 60 if span > 0 else 0.0
    eta_h = (TOTAL - done) / done * span / 3600 if done and span else float("nan")
    idle = time.time() - max(ts) if ts else float("nan")

    print(f"\n=== Stage-1 code-domain run @ {time.strftime('%H:%M:%S')} ===")
    print(f"cells: {done}/{TOTAL} ({100*done/TOTAL:4.1f}%)  |  ok {ok}  fail {fail}"
          f"  |  {rate:4.1f} cells/min  |  ETA ~{eta_h:4.1f} h  |  last write {idle:4.0f}s ago")
    okc = defaultdict(int); dnc = defaultdict(int)
    for (it, m, la, co, ca, rp, pr), v in cell.items():
        dnc[m] += 1; okc[m] += 1 if v else 0
        dnc[(m, pr)] += 1; okc[(m, pr)] += 1 if v else 0
    print(f"  {'model':30s} {'done/total':>12s}  {'ok':>5s} {'fail':>5s}   "
          f"{'score_only':>12s} {'verify_written':>14s}")
    for m in MODELS:
        so_ok, so_dn = okc[(m, 'score_only')], dnc[(m, 'score_only')]
        vw_ok, vw_dn = okc[(m, 'verify_written')], dnc[(m, 'verify_written')]
        print(f"  {m:30s} {dnc[m]:5d}/{PER_MODEL:<6d}  {okc[m]:5d} {dnc[m]-okc[m]:5d}   "
              f"{so_ok:4d}/{so_dn:<4d}   {vw_ok:5d}/{vw_dn:<4d}"
              + ("   <-- high failure" if dnc[m] and (dnc[m]-okc[m]) / dnc[m] > 0.15 else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", type=int, default=0,
                    help="refresh every N seconds (e.g. 600 for every 10 min); 0 = one snapshot")
    ap.add_argument("--path", default=OBS)
    a = ap.parse_args()
    if a.watch <= 0:
        snapshot(a.path)
        return
    try:
        while True:
            snapshot(a.path)
            time.sleep(a.watch)
    except KeyboardInterrupt:
        print("\n(monitor stopped)")


if __name__ == "__main__":
    main()
