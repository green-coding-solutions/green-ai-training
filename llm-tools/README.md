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
| Updating the facts | retrain | re-copy one Markdown file | edit one Markdown file, restart the chat |

Use `ollama-rag.py` when you want to keep your own model, don't want to load the full skill into a small context
window, and want the energy figures to come straight from the measurements. The model never has to remember a number.
It gets the fact, including its conditions and caveats, as the tool result and is told to quote only that.

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/download) running locally (`ollama serve`, or the Ollama desktop app)
- A model that supports tool calling, pulled with `ollama pull <model>` (see [Choosing a model](#choosing-a-model))
- The rest of this repository: the script reads the facts from `../dataset/spec/measured-facts.md`, so keep it inside
  the `llm-tools/` folder of the repository

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

## Tools available to the model

### `search_green_measurements(query)`

Searches the measured facts of this repository (Python, SQL/PostgreSQL, Bash, web/browser, containers, compression).

- `query`: keywords such as `string concatenation join`, `bulk insert postgres`, `gzip zstd`, or a fact ID like
  `F-STRCAT`.
- Returns up to 3 matching facts, each with its section, the measured figures, the conditions and the measurement and
  benchmark links.
- If nothing matches, it returns the list of all fact IDs, so the model can search again with an ID.

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
- **Keyword retrieval:** facts are found by matching words, not by embeddings in a vector database. Each fact is short and
  covers one technique, so with a few dozen of them, matching words is enough and needs no embedding model or index.
- **Whole facts, not chunks:** the unit of retrieval is one complete fact with its figures, conditions and links, never
  a cut-off text fragment.

`get_pull_request` is plain tool use rather than RAG: it fetches data for the model to work on, not knowledge to base
an answer on.

Step by step:

1. **Facts:** at startup the script reads [`dataset/spec/measured-facts.md`](../dataset/spec/measured-facts.md).
   Every entry that starts with `- **F-<ID>**` becomes one fact, together with its indented lines and its section
   heading. [`skill-references/measured-facts.md`](../skill-references/measured-facts.md) is only a copy of this file.
2. **System prompt:** the model is told to call `search_green_measurements` for energy questions, to base its answer
   only on the returned figures, to name Green Metrics Tool as the source with the measurement link, and to say so when
   no measurement fits.
3. **Retrieval:** the search is a keyword match, not a vector search. Query and facts are split into words, common
   words (*energy*, *saving*, *how*, …) are dropped and simple plural and *-ing*/*-ed* endings removed. A query word
   counts as a hit when it equals a fact word or one is the prefix of the other (*postgres* finds *PostgreSQL*).
   The facts with the most hits are returned, as long as they match at least two thirds as many words as the best one.
4. **Tool loop:** the script runs the tool calls, sends the results back to the model and repeats until the model
   answers without a tool call.

## Choosing a model

The model has to support tool calling. On [ollama.com/search?c=tools](https://ollama.com/search?c=tools) you can
filter for models that do. Larger models decide more reliably when to call the tool and stick more closely to the
returned figures. A temperature around 0.2 helps here, too (see the main [README](../README.md#recommended-setting-temperature-02)).

Some models (e.g. `qwen2.5-coder`) don't return structured tool calls but write the call as JSON into their answer.
The script recognizes these calls as well and runs them. Because the answer streams, you see this JSON in the terminal
before the tool result.

## Limitations

- **Keyword search only:** there are no synonyms. *docker image* does not find the container image fact, because the
  fact never says *docker*. Rephrase (*container image*) or let the model search with a fact ID. See
  [Possible upgrade: BM25 ranking](#possible-upgrade-bm25-ranking) for how the search could grow with more facts.
- **Figures are not scaled:** the facts are micro-benchmark results on dedicated lab machines. They show the order of
  magnitude and direction of a saving, not an exact figure for your code or hardware.
- **Large pull requests:** diffs longer than 20,000 characters are truncated, and only the first 100 comments of each
  kind are fetched.

## Possible upgrade: BM25 ranking

The current ranking counts how many query words a fact contains. That works for a few dozen facts, but gets weaker as
`measured-facts.md` grows:

- Every word counts the same. A word that appears in many facts (*Python*, *loop*, *rows*) weighs as much as a rare,
  telling one (*lru_cache*, *COPY*).
- Long facts match more words by chance and push short, more precise facts down.

[BM25](https://en.wikipedia.org/wiki/Okapi_BM25), the standard ranking in classic search engines, fixes both: it gives
rare words more weight than common ones and corrects for fact length. It is still keyword search, so it fits into
`search_green_measurements` without embeddings or a vector database. Either implement it in about 30 lines of Python or
use the [`rank_bm25`](https://pypi.org/project/rank-bm25/) package. Facts and tokenizer stay as they are, and the
fact ID lookup and the list of IDs on no match can stay too.

BM25 only matches exact words after tokenizing. The prefix matching (*postgres* finds *PostgreSQL*) would have to come
from a proper stemmer or a small synonym table instead. BM25 doesn't solve synonyms (*docker* vs. *container*) either.
If that ever matters more than ranking, embeddings or a hybrid of BM25 and embeddings are the next step.

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
