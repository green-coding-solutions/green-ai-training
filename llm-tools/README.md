# Green Coding RAG chat for Ollama

`ollama-rag.py` is a terminal chat for any local [Ollama](https://ollama.com/download) model. When you ask about the
energy use of a coding technique, the model calls a tool that looks up the matching measurement from this repository
and answers with the measured figures and the link to the Green Metrics Tool run.

```
You: How much energy does string building with join save in Python?

[Tool call: search_green_measurements({'query': 'string building join'})]
[Tool result: [Python] **F-STRCAT**: Building a string from 1,000,000 pieces with `+=` used ~469 J; ...]

Assistant: In Green Metrics Tool micro-benchmarks, building a string from 1,000,000 pieces ...
```

**Contents**

- [When to use it](#when-to-use-it)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Live measurements and fallback](#live-measurements-and-fallback)
- [Tools available to the model](#tools-available-to-the-model)
- [How it works](#how-it-works)
- [Choosing a model](#choosing-a-model)
- [Limitations](#limitations)
- [Possible upgrade: BM25 ranking](#possible-upgrade-bm25-ranking)
- [Sample conversation](#sample-conversation)

## When to use it

The repository offers three ways to bring the measurements into an LLM:

| | Fine-tuned models | [`SKILL.md`](../SKILL.md) | `ollama-rag.py` |
|---|---|---|---|
| Model | our fine-tuned models | any capable LLM (Claude, ChatGPT, …) | **any** local Ollama model with tool calling |
| Training needed | yes | no | no |
| Context used | none | the whole skill and facts file with each task | only the facts that match the question |
| Where the numbers come from | learned during training | the facts file in the context | returned by a tool call, word for word |
| Updating the facts | retrain | re-copy one Markdown file | newest values are fetched live on every lookup |

Use `ollama-rag.py` when you want to keep your own model, don't want to load the full skill into a small context
window, and want the energy figures to come straight from the measurements. The model never has to remember a number.
It gets the fact, including its conditions and caveats, as the tool result and is told to quote only that.

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/download) running locally (`ollama serve`, or the Ollama desktop app)
- A model that supports tool calling, pulled with `ollama pull <model>` (see [Choosing a model](#choosing-a-model))
- The rest of this repository: the script reads the stored facts from `../dataset/spec/measured-facts.md`, so keep it
  inside the `llm-tools/` folder of the repository, together with `include/` and `fact-lookup.json`
- Internet access to `api.green-coding.io` for the newest values (optional: without it the stored facts are used)

## Installation

```bash
cd llm-tools
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull gemma4
```

## Usage

```bash
python3 ollama-rag.py                         # default model: gemma4
python3 ollama-rag.py --model qwen3:8b        # any other Ollama model
python3 ollama-rag.py --model gemma4:12b-mlx  # a specific tag, e.g. the MLX build on Apple Silicon
python3 ollama-rag.py --help
```

| Option | Default | Description |
|---|---|---|
| `--model` | `gemma4` | Name of the Ollama model to chat with, exactly as `ollama list` shows it |

Commands inside the chat:

| Command | Description |
|---|---|
| `/clear` | Forget the conversation and start over (the system prompt stays) |
| `/exit` | Quit |

Responses stream token by token. Every tool call and its result is printed in brackets, so you can see exactly which
measurement the answer is based on.

**Example questions**

- *How much energy does `"".join()` save compared to `+=`?*
- *Is `SELECT *` really worse than naming the columns?*
- *Should I use gzip or zstd for my log files?*
- *Does lazy loading images save energy?*
- *Review PR 1234 in green-coding-solutions/green-metrics-tool for energy problems.*

## Live measurements and fallback

The benchmarks behind the facts keep running on the Green Metrics Tool cluster, so their energy values move. The chat
therefore looks up the newest values whenever a fact is found:

1. **Static lookup:** [`fact-lookup.json`](fact-lookup.json) lists, for every fact in `measured-facts.md`, the keywords
   that trigger it and the Green Metrics Tool tasks it was measured with (task ID, software ID and name):

   ```json
   "F-STRCAT": {
     "keywords": ["string building", "string concatenation", "+=", "join", "f-string", ...],
     "tasks": [
       {"id": 248, "software_id": 48, "name": "String Concatenation - += (optimized)"},
       ...
     ]
   }
   ```

2. **Live fetch:** for a matching fact, the script calls `https://api.green-coding.io/v1/software/<software_id>/tasks`
   for the softwares of its tasks. The API returns the newest successful run of every task with its phase metrics, the
   same selection `data/query.sql` uses for the export. Each software is fetched once per chat session.
3. **Fresh value or stored fact:** every task with a fresh value is shown with CPU energy, machine energy (where the
   machine has a power meter), duration, work units (iterations, rows, page loads, …) and the link to its run. If a
   task has no fresh value, because the API is unreachable, returns an error or has no run with energy values, the
   stored fact from `measured-facts.md` is added as well. If the network is down, the first failed request switches
   the whole search to the stored facts, so you wait for at most one timeout.

A result with live values:

```
[Web / browser] F-ANIM
Newest measurements from the Green Metrics Tool API:
On GUI Benchmarking - TX1330 M3 [PREMIUM]:
- JS Animation - Clean (Run Only) (phase Run animation for 20 seconds): CPU energy 155 J, machine energy 780 J, duration 20.1 s; run of 2026-10-22: https://metrics.green-coding.io/stats.html?id=...
- CSS Animation - Clean (Run Only) (phase Run animation for 20 seconds): CPU energy 144 J, machine energy 771 J, duration 20.1 s; run of 2026-10-22: https://metrics.green-coding.io/stats.html?id=...
```

The same lookup without network access:

```
[GMT API not reachable (...), using the stored facts]
[Web / browser] F-ANIM
Stored measurement from measured-facts.md:
**F-ANIM**: A 20-second animation in a real browser: JavaScript `requestAnimationFrame` with style updates ~161 J ...
```

**Adding a fact:** write it in `measured-facts.md`, then add an entry with the same ID to `fact-lookup.json`. Task IDs
and software IDs are in the Green Metrics Tool export
([`data/green-coding-measurement-data.csv`](../data/green-coding-measurement-data.csv), columns 1 and 3).

## Tools available to the model

### `search_green_measurements(query)`

Searches the measured facts of this repository (Python, SQL/PostgreSQL, Bash, web/browser, containers, compression).

- `query`: keywords such as `string concatenation join`, `bulk insert postgres`, `gzip zstd`, or a fact ID like
  `F-STRCAT`.
- Returns up to 3 matching facts: the newest values from the Green Metrics Tool API with their run links, or the stored
  fact with its figures, conditions and links (see [Live measurements and fallback](#live-measurements-and-fallback)).
- If nothing matches, it returns the list of all fact IDs with their first keywords, so the model can search again.

### `get_pull_request(owner, repo, pr_number)`

Fetches a GitHub pull request for review: title, author, state, branches, size, description, the diff, the
conversation comments and the inline review comments. The model then reviews it and can look up measurements for the
patterns it finds.

Without a token GitHub allows 60 API requests per hour (one PR fetch uses 4). For private repositories or more
requests, set a token before you start the chat:

```bash
export GITHUB_TOKEN=ghp_...
python3 ollama-rag.py
```

## How it works

This is *agentic RAG* (retrieval-augmented generation through a tool call) with keyword retrieval:

- **Agentic:** the model decides when to look something up. Most RAG setups retrieve on every question
  and always put the results into the prompt. Here, retrieval runs only when the model calls `search_green_measurements`.
- **Keyword retrieval:** facts are found through a hand-written keyword list per fact, not by embeddings in a vector
  database. With a few dozen facts that cover one technique each, matching words is enough and needs no embedding model
  or index.
- **Live data:** the retrieved fact points to its Green Metrics Tool tasks, whose newest values are fetched at
  question time. The stored fact text is the fallback.

`get_pull_request` is plain tool use rather than RAG: it fetches data for the model to work on, not knowledge to base
an answer on.

Files:

| File | Content |
|---|---|
| `ollama-rag.py` | The chat: command line options, system prompt, streaming, tool loop |
| `include/green_search.py` | The `search_green_measurements` tool: keyword lookup, live fetch from the GMT API, fallback to the stored facts |
| `include/github_pr.py` | The `get_pull_request` tool |
| `fact-lookup.json` | Keywords and GMT tasks per fact |

Every include defines its tool schema as `TOOL` and the function that runs it. To add a tool, put a new file into
`include/` and register both in `ollama-rag.py` (`tools` and `available_functions`).

Step by step:

1. **Startup:** the script reads the stored facts from
   [`dataset/spec/measured-facts.md`](../dataset/spec/measured-facts.md) (every entry that starts with `- **F-<ID>**`,
   with its indented lines and section heading) and the static lookup [`fact-lookup.json`](fact-lookup.json).
   [`skill-references/measured-facts.md`](../skill-references/measured-facts.md) is only a copy of the facts file.
2. **System prompt:** the model is told to call `search_green_measurements` for energy questions, to base its answer
   only on the returned figures, to name Green Metrics Tool as the source with the measurement link, and to say so when
   no measurement fits.
3. **Retrieval:** query and keywords are split into words, common words (*energy*, *saving*, *how*, …) are dropped and
   simple plural and *-ing*/*-ed* endings removed. A query word counts as a hit when it equals a keyword word or one is
   the prefix of the other (*postgres* finds *postgresql*). The facts with the most hits are returned, as long as they
   match at least two thirds as many words as the best one. A fact ID such as `F-STRCAT` finds its fact directly.
4. **Live values:** for each fact found, the newest values of its tasks are fetched, or the stored fact is used (see
   [Live measurements and fallback](#live-measurements-and-fallback)).
5. **Tool loop:** the script runs the tool calls, sends the results back to the model and repeats until the model
   answers without a tool call.

## Choosing a model

The model has to support tool calling. On [ollama.com/search?c=tools](https://ollama.com/search?c=tools) you can
filter for models that do. Larger models decide more reliably when to call the tool and stick more closely to the
returned figures. A temperature around 0.2 helps here, too (see the main [README](../README.md#recommended-setting-temperature-02)).

Some models (e.g. `qwen2.5-coder`) don't return structured tool calls but write the call as JSON into their answer.
The script recognizes these calls as well and runs them. Because the answer streams, you see this JSON in the terminal
before the tool result.

## Limitations

- **Keywords are maintained by hand:** a question only finds a fact if it shares a word with that fact's keywords.
  Add missing terms to `fact-lookup.json`. See [Possible upgrade: BM25 ranking](#possible-upgrade-bm25-ranking) for how
  the search could grow with more facts.
- **Live values come without the caveats:** when all tasks of a fact have live values, the model gets the task names
  and figures only, not the conditions and caveats written in the fact text (e.g. that caching only pays off with
  repeated inputs). Ratios such as *about 260× less* have to be worked out from the figures.
- **New benchmarks are not picked up:** only the tasks listed in `fact-lookup.json` are fetched. A new benchmark needs
  a new fact in `measured-facts.md` and a lookup entry.
- **Long tool results:** facts that link many tasks return a lot of text. The compression codec comparison
  (F-COMPRESS-CODECS, 56 tasks) returns about 12,000 characters, which can fill the context window of small models.
- **Figures are not scaled:** the facts are micro-benchmark results on dedicated lab machines. They show the order of
  magnitude and direction of a saving, not an exact figure for your code or hardware.
- **Large pull requests:** diffs longer than 20,000 characters are truncated, and only the first 100 comments of each
  kind are fetched.

## Possible upgrade: BM25 ranking

The current ranking counts how many query words appear in a fact's keywords. That works for a few dozen facts, but
gets weaker as `measured-facts.md` grows:

- Every word counts the same. A word that appears in many keyword lists (*postgresql*, *compression*, *gzip*) weighs as
  much as a rare, telling one (*lru_cache*, *executemany*).
- Long keyword lists match more words by chance and push short, more precise ones down.

[BM25](https://en.wikipedia.org/wiki/Okapi_BM25), the standard ranking in classic search engines, fixes both: it gives
rare words more weight than common ones and corrects for fact length. It is still keyword search, so it fits into
`search_green_measurements` without embeddings or a vector database. Either implement it in about 30 lines of Python or
use the [`rank_bm25`](https://pypi.org/project/rank-bm25/) package. The lookup file, the tokenizer, the live fetch
and the fallback stay as they are. With many more facts, indexing the fact text next to the keywords saves
writing every term by hand.

BM25 only matches exact words after tokenizing. The prefix matching (*postgres* finds *postgresql*) would have to come
from a proper stemmer instead. Synonyms (*docker* vs. *container*) still need the keyword list. If that ever becomes
too much to maintain, embeddings or a hybrid of BM25 and embeddings are the next step.

## Sample conversation


```log
$ python3 ollama-rag.py --model gemma4:12b-mlx
Chat started with gemma4:12b-mlx
Commands: /clear, /exit

You: How much saving do I get when I use COPY in PostgreSQL vs calling single inserts on a 1.000 insert batch?

Assistant:


[Tool call: search_green_measurements({'query': 'SQL bulk insert COPY vs single insert'})]
[Tool result: [SQL (PostgreSQL 16, Python client with psycopg 3, client and server on the same machine)]
**F-PG-INSERT**: Inserting 500,000 rows as 100 batches of 5,000 rows (one commit per batch): one `execute()` per row
~384 J and 60 s, `executemany()` ~139 J (about 2.8× less), `COPY ... FROM STDIN` ~17 J and 3.1 s (about 22× less than
the loop, about 8× less than `executemany`). With batches of 1,000 rows, COPY used about 5× less than the loop.
With batches of only 100 rows the differences were small (loop ~13 J, `executemany` ~15 J, COPY ~9.5 J), because
per-batch overhead dominates. Batch writes pay off with many rows per batch.
Measurements: https://metrics.green-coding.io/compare-simple.html?ids=8e80b599-3332-432f-8c7e-1cfb93a3a354,8b4c205d-5fb1-40af-ab77-0427ca572f4e,adff4e53-2f1a-4d88-9c0d-dd681d02923f
Benchmark: https://github.com/green-coding-solutions/green-ai-training/tree/main/benchmarks/sql]


Assistant: When using `COPY` in PostgreSQL compared to single inserts for a batch of 1,000 rows, the energy savings are approximately **5× less**.

These figures come from Green Metrics Tool micro-benchmarks:
*   **COPY ... FROM STDIN**: ~9.5 J (for 100 rows)
*   **executemany()**: ~15 J (for 100 rows)
*   **one `execute()` per row**: ~13 J (for 100 rows)

Note: With batches of only 100 rows, the differences are small because per-batch overhead dominates. Batch writes provide significantly higher efficiency as the number of rows per batch increases.

Measurements: https://metrics.green-coding.io/compare-simple.html?ids=8e80b599-3332-432f-8c7e-1cfb93a3a354,8b4c205d-5fb1-40af-ab77-0427ca572f4e,adff4e53-2f1a-4d88-9c0d-dd681d02923f

```
