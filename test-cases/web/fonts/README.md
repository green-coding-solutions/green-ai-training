# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Replace the six self-hosted TrueType font files (~650 KB each, ~4 MB in total) with a system font stack (`font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`), so no font file has to be downloaded at all
- If the brand font must stay: load a single subsetted WOFF2 file (variable font or only the weights really used) with `font-display: swap` instead of six full TTF files, and synthesize or drop rarely used styles (Light, Black, Bold Italic)
- Expected energy saving when running this file 1.000 times

Fonts: Lato by Łukasz Dziedzic, SIL Open Font License 1.1 (see `fonts/OFL.txt`). All files are local, no remote font service is used.
