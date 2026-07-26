#!/usr/bin/env python3
"""Regenerate every CCC figure from the committed evidence, and verify each one
still reproduces its published numbers.

    python3 experiments/make_all_ccc_figures.py [DATA_ROOT]

DATA_ROOT defaults to the repo root. Every figure script recomputes its
estimates from the raw *_obs.jsonl rows and prints a validation block; this
driver fails loudly if any validation line reports a mismatch, so a silent
divergence between the figures and the findings cannot survive a run.
"""
import subprocess, sys, pathlib

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = pathlib.Path(__file__).parent

FIGURES = [
    ("make_ccc_explainer_figure.py", "fig_ccc_explainer.png",  "§4   explainer triptych — the ruler, the failure, the fix"),
    ("make_ccc_mechanism_figure.py",  "fig_ccc_mechanism.png",  "§5   mechanism — the conclusion is the active ingredient"),
    ("make_ccc_frontier_figure.py",   "fig_ccc_frontier.png",   "§6.4 frontier tier — capture survives, SQL is the common failure"),
    ("make_ccc_openrouter_figure.py", "fig_ccc_openrouter.png", "§6.5 open-weight arms — one wrong reference flips the verdict"),
    ("make_ccc_reversal_plain.py", "fig_ccc_reversal_plain.png", "§6.5 plain-language twin — for a newcomer audience"),
    ("make_ccc_architecture_figure.py", "fig_ccc_architecture.png", "§7   mitigations — only isolation closes the pathway"),
]

failed = []
for script, out, label in FIGURES:
    print(f"\n{'=' * 78}\n{label}\n{'-' * 78}")
    p = subprocess.run([sys.executable, str(HERE / script), ROOT,
                        str(HERE / out)], capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        sys.stdout.write(p.stderr)
        failed.append((script, "crashed"))
    elif "MISMATCH" in p.stdout:
        failed.append((script, "validation mismatch"))

print(f"\n{'=' * 78}")
if failed:
    for s, why in failed:
        print(f"FAIL  {s}: {why}")
    sys.exit(1)
print(f"all {len(FIGURES)} figures regenerated; every validation check passed")
