# Prompt

Optimize the build of this project according to Green Coding Rules

# Expected Output

- Replace the plain `cp` build step with a minifying build, e.g. `esbuild src/booking.js --minify --outfile=dist/booking.js` and `esbuild src/booking.css --minify --outfile=dist/booking.css` (or terser / lightningcss), so comments, whitespace and long local names are not shipped to every visitor
- Remove the debug `console.log` calls from the production build (e.g. esbuild `--drop:console`)
- Do not ship source maps to production (or serve them only to developers)
- Expected energy saving when running this file 1.000 times
