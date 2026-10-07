#!/usr/bin/env bash
# Builds the Latin-subset WOFF2 files used by index-woff2.html from the TTFs in test-cases/web/fonts/fonts.
# Needs: pip install fonttools brotli
set -euo pipefail
SRC="$(dirname "$0")/../../../test-cases/web/fonts/fonts"
OUT="$(dirname "$0")/fonts"
mkdir -p "$OUT"
for weight in Regular Bold; do
  pyftsubset "$SRC/Lato-$weight.ttf" \
    --unicodes="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122" \
    --layout-features='kern,liga' --flavor=woff2 --output-file="$OUT/Lato-$weight-latin.woff2"
done
