#!/usr/bin/env python3
"""Regenerate SHA256SUMS.md, the hash manifest that binds the paper to its evidence.

    python3 experiments/make_sha256_manifest.py [--check]

One external timestamp on the manifest fixes the whole set in time, because every
artifact is bound to it by hash. That only holds while the hashes are current, so
the manifest has to be regenerated whenever the paper, a figure or the tooling
changes -- it was hand-built once and broke on the very next edit to the source.

Order of operations when the paper changes:

    python3 experiments/make_all_ccc_figures.py    # figures, with validation
    paper/build_pdf.sh paper/Contextual_Conclusion_Capture.pdf
    python3 experiments/make_sha256_manifest.py

--check verifies the existing manifest instead of rewriting it, and exits
non-zero if any file has moved or gone missing. Use it before archiving.
"""
import hashlib, pathlib, re, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "SHA256SUMS.md"

SECTIONS = [
    ("paper and tooling", [
        "paper/contextual_conclusion_capture.md",
        "paper/Contextual_Conclusion_Capture.pdf",
        "paper/REFERENCES_verified.md",
        "paper/render_paper.py",
        "paper/build_pdf.sh",
        "experiments/FIGURES.md",
        "experiments/make_all_ccc_figures.py",
        "experiments/check_isolation_null_calibration.py",
        "experiments/check_no_reference_baseline.py",
        "experiments/make_sha256_manifest.py",
    ]),
    ("figures", sorted(
        str(p.relative_to(ROOT)) for p in (ROOT / "experiments").glob("fig_ccc_*.png"))),
    ("raw evidence", sorted(
        str(p.relative_to(ROOT)) for p in (ROOT / "experiments/results").glob("*_obs*.jsonl"))),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "(not a git checkout)"


if "--check" in sys.argv:
    if not OUT.exists():
        sys.exit("SHA256SUMS.md does not exist; run without --check to create it")
    bad = missing = ok = 0
    for line in OUT.read_text().splitlines():
        m = re.match(r"^([a-f0-9]{64})  (.+)$", line)
        if not m:
            continue
        digest, rel = m.groups()
        path = ROOT / rel
        if not path.exists():
            print(f"MISSING   {rel}"); missing += 1
        elif sha256(path) != digest:
            print(f"CHANGED   {rel}"); bad += 1
        else:
            ok += 1
    print(f"\n{ok} verified, {bad} changed, {missing} missing")
    if bad or missing:
        print("\nThe manifest no longer describes this tree. Rebuild the PDF and rerun\n"
              "this script without --check before archiving or timestamping.")
        sys.exit(1)
    sys.exit(0)

lines = [
    "# SHA-256 manifest — Contextual Conclusion Capture",
    "",
    f"Git commit: {commit()}",
    f"Generated:  {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    "",
    "Timestamp THIS FILE to fix the whole set in time: every artifact below is bound",
    "to it by hash, so one timestamp covers the paper, the figures and the raw",
    "evidence. Verify any single file with:",
    "",
    "    sha256sum -c --ignore-missing SHA256SUMS.md",
    "",
    "Or check the whole manifest, which also catches files that have gone missing:",
    "",
    "    python3 experiments/make_sha256_manifest.py --check",
    "",
    "Regenerate it with the same script and no argument, after rebuilding the",
    "figures and the PDF. A manifest is only worth as much as its currency.",
    "",
    "```",
]
n = 0
for title, files in SECTIONS:
    lines.append(f"# {title}")
    for rel in files:
        path = ROOT / rel
        if not path.exists():
            print(f"warning: skipping missing {rel}", file=sys.stderr)
            continue
        lines.append(f"{sha256(path)}  {rel}")
        n += 1
    lines.append("")
lines[-1] = "```"

OUT.write_text("\n".join(lines) + "\n")
print(f"wrote {OUT.relative_to(ROOT)} — {n} files hashed")
