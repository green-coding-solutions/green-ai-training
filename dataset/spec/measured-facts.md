# Measured Facts

Figures derived from `../../data/green-coding-measurement-data.csv` (Green Metrics Tool, export of 14 October 2026, query
in `../../data/query.sql`). Values are CPU energy (RAPL, whole CPU package) unless noted, "machine energy" is the AC power
meter of the whole machine. Python, SQL, bash and container micro-benchmarks ran on the "Micro Benchmarking" cluster
machine (DVFS off, TurboBoost off, HT off), browser and web server benchmarks on the "GUI Benchmarking" machine,
compression and preview environments on the "High Performance" machine. Benchmark definitions are in `../../benchmarks/`
(compression: SEBOM repository). All runs are public in the
[Green Metrics Tool dashboard](https://metrics.green-coding.io/runs.html?&uri=green-ai-training&show_archived=false&show_other_users=true),
machine specs in the [cluster status](https://metrics.green-coding.io/cluster-status.html).
The export contains energy and duration per phase only. Work units (rows, iterations, MB, page loads) come from the
usage scenarios.

Rules for using these facts in training data:
- Quote only the rounded figures written here, always with source ("in Green Metrics Tool micro-benchmarks") and
  condition. Never scale them to the user's workload.
- Each example that quotes a figure lists the fact ID(s) in its `facts:` field. `verify.py` checks that every
  energy, percentage or multiplier number in the assistant text appears in a cited fact.
- Every fact ends with its sources: **Measurements** links the Green Metrics Tool run(s) (a comparison table when there
  are several), **Benchmark** links the usage scenarios. When an answer quotes a figure, it may add one of these links
  verbatim so the user can check the measurement. Never shorten, combine or invent a link: `verify.py` rejects any
  `metrics.green-coding.io` or `github.com/green-coding-solutions` link that is not in a cited fact.

## Python

- **F-STRCAT**: Building a string from 1,000,000 pieces with `+=` used ~469 J; `"".join()` used ~1.8 J.
  That is roughly 260× less CPU energy for `join`. f-string concatenation in a loop behaved like `+=` (~455 J).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=732b88b3-e081-409d-a987-d1a929b357e4,527c0154-dbb1-4c82-b98f-838f994af603,2fca8771-9ad9-4ec0-b51f-2ee78ee20865
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-LISTINS**: 1,000,000 × `list.insert(0, x)` used ~1515 J, 1,000,000 × `list.append(x)` used ~1.2 J
  (over 1000× difference), because every front insert shifts the whole list.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=1da9c13d-364b-4f71-b23f-785bf1caeac8,75a7d151-3a7b-4575-b3e1-de125ce00d00
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-LRU**: 1,000,000 repeated computations: uncached ~43 J, with `@functools.lru_cache` ~4.7 J (about 9× less).
  This benchmark draws inputs from only 200 distinct values. With mostly unique inputs, caching only adds overhead.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=ddf98f50-15ee-48e2-ab38-cc89acc88142,808b9a2c-1abf-4af5-9b04-3a6ce700fcdb
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-REGEX**: 1,000,000 matches: inline `re.match(pattern, s)` ~21 J, precompiled pattern ~18 J (about 18% less),
  because `re` caches compiled patterns internally. Forcing a recompile on every call costs about 200× more per match.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=3827c15a-4295-44a4-8025-a07e8653ab7e,b7a9f0bd-c9e0-4b95-9bda-e8a96f38020c,f3e0434d-744b-41a0-a0cc-9bf00d80500d
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-ATTR**: Caching `math.sqrt` in a local variable before a 10,000,000-iteration loop saved about 4-5%.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=349ba1de-3013-4ceb-b793-8abe687a8912,a9155140-fa91-43ef-90da-fa8c4711224b
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-COND**: 10,000,000 classifications: simple equality branches used ~46 J, complex range/modulo conditions
  ~54 J, so the simple version used about 16% less. `match` and `if/elif` with the same conditions differed by about 1%, which is noise.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=123676d7-2121-4b9d-b78e-e065836fc608,a7780e2a-2934-4d26-b2a9-2cda7848adc1
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-EXC**: 10,000,000 dict lookups with about half of the keys missing: `dict.get(key, default)` ~67 J, `try/except KeyError` ~76 J (about 12% less with
  `get`). An `if key in d` branch performed like `dict.get`. When misses are rare, `try/except` is cheap, because the cost is in raising.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=4753302a-710f-4132-8001-9da3ba960d13,d7ded3f2-f9e7-4781-905e-9782a8305b8f,8f054455-adbc-402d-b593-0191d1061cd8
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-MEMB**: A *single* membership test on a 10,000,000-element list (~6.9 J) was cheaper than converting the list to a
  set first and testing once (~10.5 J, about 50% more). A set only pays off when you look up many times.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=70871c0f-e630-4755-a459-b98e5d4031f2,722fea72-6f69-4acb-8ce7-632caeb444f4
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-NOGRAD**: 100,000 PyTorch CPU inferences: without `torch.no_grad()` ~157 J, with it ~135 J (about 14% less).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=42de8e68-4536-43f4-a9bd-427ec42affd1,7e6a3886-425a-4992-9f14-180bede2d841
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-NUMBA**: Quantizing 10,000,000 samples in a pure Python loop ~40 J, with Numba `@njit` ~9.5 J (about 4× less).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=dc2ed71b-e8ed-48d5-be04-0dd9dfe1443f,2b9e7f88-4aad-42ee-a9e6-25ff4e6ea712
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-HTTP**: 10 HTTP requests: sync `urllib` ~9.1 J and 3.1 s, async `httpx` ~8.4 J and 2.6 s. That is about 7% less
  CPU energy and about 17% less wall time. For small request counts the gain is mostly wall time.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=97acc9a0-3856-4bbb-b816-2b64030fba98,6415cccb-ad1a-4d87-ae46-92740c5e285b
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python
- **F-IMPORT**: 1,000 Python process starts that each import a module: `from sympy import *` ~3103 J and
  `import sympy` ~3093 J, `from posix import *` and `import posix` both ~121 J. Star imports and namespace imports showed
  no measurable energy difference. Changing star imports is therefore not a green optimization: leave existing star
  imports unchanged and say that it makes no measurable difference.
  What costs energy is loading a heavy module at all: a start with `sympy` used about 3.1 J and 0.54 s, about 25× a
  start that imports only a built-in module (~0.12 J).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=b8705e55-3144-4871-8d37-0835189905ae,a347d140-8e85-456b-bf57-f8c77373c8fa
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/python

## SQL (PostgreSQL 16, Python client with psycopg 3, client and server on the same machine)

- **F-PG-INSERT**: Inserting 500,000 rows as 100 batches of 5,000 rows (one commit per batch): one `execute()` per row
  ~384 J and 60 s, `executemany()` ~139 J (about 2.8× less), `COPY ... FROM STDIN` ~17 J and 3.1 s (about 22× less than
  the loop, about 8× less than `executemany`). With batches of 1,000 rows, COPY used about 5× less than the loop.
  With batches of only 100 rows the differences were small (loop ~13 J, `executemany` ~15 J, COPY ~9.5 J), because
  per-batch overhead dominates. Batch writes pay off with many rows per batch.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=8e80b599-3332-432f-8c7e-1cfb93a3a354,8b4c205d-5fb1-40af-ab77-0427ca572f4e,adff4e53-2f1a-4d88-9c0d-dd681d02923f
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/sql
- **F-PG-SELECT**: Reading rows 1,000 times from a 52-column products table with large text columns:
  `SELECT *` vs. naming the 10 needed columns: 500 rows ~95 J vs ~17 J (about 5.5× less), 2,500 rows ~470 J vs ~64 J
  (about 7× less), 10,000 rows ~1869 J vs ~274 J (about 7× less). For a JOIN of orders and order items (fewer, smaller
  columns) the gap was smaller: 200 rows ~34 J vs ~15 J (about 2.3× less), 1,000 rows ~153 J vs ~39 J (about 4× less).
  The saving grows with the size of the columns you skip.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=b7203ffe-39ae-4e84-bf85-998c9389ea46,4702c2ee-13d5-4d70-bcfe-31e193104a8e
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/sql
- **F-PG-COLUMNS**: 2,500 rows read 1,000 times: 1 column ~13 J, 2 columns ~19 J, 4 columns ~32 J, 8 columns ~58 J,
  all 52 columns (`SELECT *`) ~465 J, about 8× the 8-column query. Cost scales with the data each column carries.
  Measurements: https://metrics.green-coding.io/stats.html?id=a6b398b6-6d87-4aff-a9fb-979ad99a642c
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/sql

## Bash

- **F-BASH-QUOTES**: Assigning a 6,200-character literal in a loop: with 1,000,000 iterations double quotes used ~314 J,
  single quotes ~237 J (about 24% less). With 100,000 iterations also about 24% less, with 10,000 iterations about 14%
  less. A second machine ("High Performance") confirmed it: about 24% less over the whole run. Bash scans double-quoted
  text for `$`, backticks and backslashes, single-quoted text is taken as is. Recommendation: single quotes for every
  literal that needs no expansion. The absolute saving is small for short strings in scripts that run once, and grows
  with literal length and loop count.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=dd9bbb4e-b056-4067-8ad2-7b1818a86f10,b265ef9b-adb9-4b56-a14b-ae34fdaa7247,28d92c15-79d7-44ca-8f43-a733fe2e265a,a9533378-71f0-49df-bd5f-1e5f27cda9c2
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/bash
- **F-BASH-SUBPROC**: Summarizing a 20,000-line access log (requests per status class, total bytes), identical output:
  a `while read` loop that runs `$(echo | cut)` and `$(expr)` for every field (about 10 processes per line) used
  ~1302 J and 238 s. The same loop with builtins only (`read -r` field splitting, `$(( ))`, `case`) used ~4.3 J and
  0.72 s, about 300× less. One `awk` pass over the file used ~1.0 J and 0.21 s, over 1000× less than the subprocess
  loop and about 4× less than the builtin loop. Process starts dominate shell scripts: avoid command substitutions
  inside loops, and hand whole-file work to one `awk`, `sort` or `grep` call.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=7ee92e8c-fd9e-46c5-8dba-2fa40de231c2,5813c30d-d074-4da0-84fc-46ab5801eaf1,b05a26a4-1f41-40ed-9cc6-9f900dee6aed
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/bash/builtins

## Web / browser

Page-load benchmarks use a headful Firefox with an empty cache on every load (first-time visitor) and an nginx
container on a local Docker network. Transferring bytes costs almost nothing there, so the figures show client and
server CPU work, not the network savings of smaller pages.

- **F-ANIM**: A 20-second animation in a real browser: JavaScript `requestAnimationFrame` with style updates ~161 J
  CPU energy, CSS `@keyframes` ~145 J (about 10% less).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=4a2085fd-6f43-4f26-a3ee-2a6fcd7db594,58ee50a2-7110-4418-beea-df6ffba5425a
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/browser/animation
- **F-IMGRENDER**: 50 page loads per format (headful browser, CPU energy): JPG ~134 J, WebP ~150 J, GIF ~151 J,
  AVIF ~159 J, PNG ~181 J. Client-side decode cost differs only moderately. AVIF decoding cost about 19% more than JPG.
  The savings of modern formats come mainly from fewer transferred bytes.
  Measurements: https://metrics.green-coding.io/stats.html?id=b31ca361-1745-4fac-8e6b-a97ec99bf476
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/image-formats
- **F-IMGENC**: Encoding 50 BMP images: JPG ~89 J, WebP ~290 J, AVIF ~658 J, GIF ~1158 J, PNG ~1257 J.
  AVIF encoding cost about 7× JPG. Encode once at build or upload time, never per request.
  Measurements: https://metrics.green-coding.io/stats.html?id=81a932bc-04da-443b-93cf-d4d8468de247
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/image-formats
- **F-DOM-SIZE**: 30 page loads of a table with 10,000 rows built from 14 elements per row (wrappers around every
  cell, rows appended to the live DOM one by one) used ~1036 J and 72 s. The same data paginated to 100 rows per page
  as a plain `<table>` built in a `DocumentFragment` used ~457 J and 36 s, about 56% less (about 2.3× less).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=fbe5f432-7318-4937-856c-60c414f0208e,608ed039-7dfb-4e27-ac7e-f091e7ca39c8
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/web/dom-size
- **F-LAZY-IMG**: An article with 15 photos (about 2 MB). Loading it 20 times without scrolling: all images eager
  ~368 J, `loading="lazy"` below the fold ~325 J (about 12% less). Loading it 10 times and scrolling to the end: eager
  ~511 J, lazy ~517 J, about 1% more, which is noise. Lazy loading only saves when visitors don't scroll to the
  images, and it should never be put on the image above the fold.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=877945eb-dd8a-48d6-9f1a-2b29980b3e31,5da76021-294f-4e78-a41e-fd3b1fcb247d
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/web/lazy-images
- **F-FONTS**: 30 cold page loads: six local TTF font files (~4 MB) ~556 J, two Latin-subset WOFF2 files (~55 KB)
  ~488 J (about 12% less), the system font stack ~410 J (about 26% less than TTF, about 16% less than WOFF2).
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=4b6e426b-ab8c-42b4-bfc5-a5e99e0c5c72,c0ffd5b6-6782-45f8-9fef-b56cc3ee45b9,856d1223-52a2-4f0a-96cf-ea17485aac39
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/web/fonts
- **F-UNUSED-CSS**: 50 cold page loads: a 16 KB stylesheet with mostly unused rules ~783 J, purged and minified to
  0.75 KB ~764 J, about 2% less, which is within measurement noise. For small stylesheets on a fast network, removing
  unused CSS makes no measurable difference in client energy. It still saves bytes on real networks.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=ec8629e6-9d04-4ca8-9da1-0e911b1faf08,bbdb2d8e-de20-445d-9a54-62aa23c45f19
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/web/unused-css
- **F-MINIFY**: 50 cold page loads of a small booking page: unminified JS and CSS sources ~837 J, an esbuild
  minified build (`--minify --drop:console`) ~822 J, about 2% less, which is within measurement noise. For small
  bundles, minification saves bytes on the network, not measurable client CPU energy.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=917d30aa-e469-4564-b413-5445847106aa,252b61b0-4e3c-4a46-96cd-5af519486361
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/web/minify
- **F-TEXT-COMPRESS**: nginx serving 2,000 requests for text assets (HTML, CSS, JS, JSON), client and server CPU energy:
  no compression ~7.3 J with 253 MB transferred, precompressed files (`gzip_static`) ~14 J with 25 MB, gzip level 5
  per request ~54 J with 29 MB. Compression sent about 10× fewer bytes. Compressing on every request cost about 7×
  the CPU energy of no compression and about 4× that of precompressed files. Precompressed files still cost about
  2× no compression, because the client has to decompress them. On the local network the transfer
  itself was almost free, so this shows only the CPU side: precompress static assets at build time, and keep
  compression on for real networks, where the byte saving is what counts.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=bac759ec-b604-4da6-b70b-3637b85f5bf4,dc5154c9-be62-4675-ba94-cecd7390807d,42f23e15-0726-4287-90c9-b242e71feb0b
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/web/text-compression

## Infrastructure

- **F-CONTAINER-IMAGE**: Building the image of a small Flask app without a build cache: `python:3.12` base with
  `build-essential`, `git`, `curl`, `vim` and dev tools (pytest, black, mypy, ipython) installed ~885 J and 157 s.
  `python:3.12-slim`, runtime dependencies only, dependency layer before the source, `pip --no-cache-dir`:
  ~124 J and 25 s, about 7× less. Serving 2,000 requests afterwards cost the same with both images (~17 J), the
  saving is in every build, pull and stored copy of the image.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=c9afc162-b9c1-4839-a5b5-1bba26f57d48,3403d83a-d61d-40aa-8dd0-8db3d62856c1
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/infra/container-image
- **F-PREVIEW-ENV**: A per-branch preview environment idling for 60 seconds: 3 app replicas, Postgres, Redis and a
  polling worker ~269 J CPU energy; 1 app replica and Postgres ~262 J, about 3% less. Machine energy differed by
  less than 1% (~1330 J vs ~1320 J), because the idle machine baseline dominates. Idle extra services cost little
  per minute. The real saving comes from environments that don't exist: tearing them down on merge and scaling to
  zero at night removes all their hours, and fewer services reserve less memory and fewer machines.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=d4a966f2-45c7-4980-b0c5-d7b8b4602102,1e82610c-494d-4686-8238-9f744f84630c
  Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/infra/minimize-environments

## Compression (CLI tools with default settings, enwik8 English text corpus, "High Performance" machine)

Defaults: gzip -6, zstd -3, lz4 -1, bzip2 -9, xz -6, lzip -6, 7-Zip default, brotli quality 11. The export has no
output sizes, so these facts compare energy only, not compression ratios. Stronger codecs usually produce smaller files.

- **F-COMPRESS**: Compressing 100 MB: gzip ~67 J, bzip2 ~106 J, brotli (CLI default = quality 11) ~3019 J,
  about 45× gzip. Decompressing 100 MB: brotli ~6.7 J, gzip ~9.1 J, bzip2 ~52 J. Brotli at max quality is fine
  for static assets compressed once, wasteful for per-request compression.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=fb08d3c3-ba41-4f0f-85fd-0b6c34e6c39b,f1479db0-c453-4aaa-9116-e137621fad07,8e93a8d2-60b0-4831-905b-764b68257bc7
  Benchmark: https://github.com/green-coding-solutions/SEBOM/tree/main/compression
- **F-COMPRESS-CODECS**: Compressing 100 MB of text: lz4 ~6 J, zstd ~16 J, gzip ~67 J, bzip2 ~106 J, xz ~458 J,
  7-Zip ~724 J, lzip ~769 J, brotli ~3019 J. zstd used about 4× less energy than gzip, xz about 29× and brotli about
  190× more than zstd. Decompressing 100 MB: lz4 ~4.1 J, zstd ~5.3 J, brotli ~6.7 J, gzip ~9.1 J, xz ~11.7 J,
  7-Zip ~19.8 J, lzip ~24.1 J, bzip2 ~52 J. Decompression is cheap for most codecs, bzip2 is the exception.
  For data compressed often (logs, backups, per-request), fast codecs like zstd or lz4 cost a fraction of the energy.
  Measurements: https://metrics.green-coding.io/compare-simple.html?ids=2584305c-7a1e-47e2-b6cc-26276962035e,addc5f5e-55da-47f8-956d-240d06304e4e,fb08d3c3-ba41-4f0f-85fd-0b6c34e6c39b,f1479db0-c453-4aaa-9116-e137621fad07,7b3bb87d-3b43-4f82-be99-0327405205b8,905bd408-6b31-4237-a4da-14b8fad90613,7f213a20-8028-4080-9583-6e465c217bb5,8e93a8d2-60b0-4831-905b-764b68257bc7
  Benchmark: https://github.com/green-coding-solutions/SEBOM/tree/main/compression
- **F-COMPRESS-BREAKEVEN** (estimate from Green Coding Solutions' CONCEPT.md, not a direct measurement):
  compressing 100 MB to 30 MB with zstd costs ~3.2 mWh. Against SSD power and embodied carbon, the stored data
  must be kept for about 0.15 days before compression pays off. With xz (~151 mWh) the break-even is about 7 days.
  Data kept only for minutes should not be compressed. The measured compression energy (F-COMPRESS-CODECS) is higher
  than this estimate assumed, so treat these break-even times as lower bounds.
  Measurements: https://metrics.green-coding.io/stats.html?id=addc5f5e-55da-47f8-956d-240d06304e4e
  Benchmark: https://github.com/green-coding-solutions/SEBOM/tree/main/compression
