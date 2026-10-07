# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Enable text compression for dynamic responses: `gzip on;` with a moderate level (e.g. `gzip_comp_level 5`) and `gzip_types` for text-based content (HTML, CSS, JavaScript, JSON, SVG, plain text), plus `gzip_min_length` so tiny responses are not compressed
- Do not compress formats that are already compressed (JPEG, PNG, WebP, AVIF, WOFF2, video)
- For the static build, pre-compress assets once at build time (e.g. Brotli at a high level or gzip -9) and serve them with `gzip_static on;` / `brotli_static on;` instead of compressing on every request. High compression levels are only worth it when the file is compressed once and served many times
- Expected energy saving when running this file 1.000 times
