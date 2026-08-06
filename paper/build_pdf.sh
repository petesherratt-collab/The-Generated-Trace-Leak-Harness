#!/usr/bin/env bash
# Build the paper as a print-ready A4 PDF.
#
#   paper/build_pdf.sh [OUT.pdf]
#
# render_paper.py converts the markdown mechanically -- no word of the source is
# altered -- and inlines the figures as data URIs, so the HTML is self-contained.
# Chromium then prints it under the stylesheet's @media print rules: no sidebar,
# forced light palette, and figures kept whole with their captions.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/Contextual_Conclusion_Capture.pdf}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

CHROME="${CHROME:-/opt/pw-browsers/chromium}"
command -v "$CHROME" >/dev/null 2>&1 || [ -x "$CHROME" ] || {
  echo "chromium not found; set CHROME=/path/to/chrome" >&2; exit 1; }

python3 "$HERE/render_paper.py" "$HERE/contextual_conclusion_capture.md" "$WORK/body.html" >/dev/null

python3 - "$WORK/body.html" "$WORK/print.html" <<'PY'
import pathlib, sys
frag = pathlib.Path(sys.argv[1]).read_text()
pathlib.Path(sys.argv[2]).write_text(
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<style>*{-webkit-print-color-adjust:exact;print-color-adjust:exact}</style>'
    '</head><body>' + frag + '</body></html>')
PY

"$CHROME" --headless --disable-gpu --no-sandbox \
  --run-all-compositor-stages-before-draw --virtual-time-budget=20000 \
  --no-pdf-header-footer --print-to-pdf="$OUT" "file://$WORK/print.html" 2>/dev/null

echo "wrote $OUT"
