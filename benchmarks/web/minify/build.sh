#!/usr/bin/env bash
# Builds the optimized variant from test-cases/web/minify/src: minified JS and CSS, console calls dropped,
# no source maps. This is the build step the test case expects instead of `cp`.
# Needs: npx (esbuild is fetched on demand)
set -euo pipefail
cd "$(dirname "$0")"
SRC=../../../test-cases/web/minify/src
ESB=${ESBUILD:-npx --yes esbuild@0.25}
mkdir -p dist
$ESB "$SRC/booking.js" --minify --drop:console --target=es2020 --log-level=warning --outfile=dist/booking.js
$ESB "$SRC/booking.css" --minify --log-level=warning --outfile=dist/booking.css
cp "$SRC/index.html" dist/index.html
