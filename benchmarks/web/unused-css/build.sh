#!/usr/bin/env bash
# Builds the optimized variant from test-cases/web/unused-css:
# keeps only the layout rules index.html uses (everything before the first component block) and minifies them.
# Needs: npx (esbuild is fetched on demand)
set -euo pipefail
cd "$(dirname "$0")"
SRC=../../../test-cases/web/unused-css
USED="$(mktemp --suffix=.css)"
trap 'rm -f "$USED"' EXIT
sed '/^\/\* ---------- carousel ---------- \*\//,$d' "$SRC/style.css" > "$USED"
${ESBUILD:-npx --yes esbuild@0.25} "$USED" --minify --log-level=warning --outfile=style.min.css
sed 's|href="style.css"|href="style.min.css"|' "$SRC/index.html" > index.html
