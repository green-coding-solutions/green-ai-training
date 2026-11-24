"""Green search tool: finds measured facts by keyword and returns the newest
Green Metrics Tool values for them, with the stored fact as fallback."""

import json
import os
import re
import urllib.error
import urllib.request

# llm-tools/, the folder above this include directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Green Metrics Tool measurements of green coding techniques. This is the
# original file, skill-references/measured-facts.md is only a copy of it.
MEASURED_FACTS_FILE = os.path.join(BASE_DIR, "..", "dataset", "spec", "measured-facts.md")
# Static lookup: per fact the keywords that trigger it and the GMT tasks
# (with their software) whose newest values are fetched online
FACT_LOOKUP_FILE = os.path.join(BASE_DIR, "fact-lookup.json")
MAX_FACT_RESULTS = 3

GMT_API = "https://api.green-coding.io"
GMT_RUN_LINK = "https://metrics.green-coding.io/stats.html?id={run_id}"

TOOL = {
    "type": "function",
    "function": {
        "name": "search_green_measurements",
        "description": (
            "Search Green Metrics Tool energy measurements of green coding techniques (Python, SQL/PostgreSQL, "
            "Bash, web/browser, containers, compression). Returns the measured energy figures and links. "
            "Use it whenever the user asks how much energy a technique uses or saves, e.g. string building, "
            "list insert, caching, SELECT *, bulk insert, image formats, lazy loading, gzip vs zstd."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords describing the technique, e.g. 'string concatenation join', or a fact ID like 'F-STRCAT'"
                }
            },
            "required": ["query"]
        }
    }
}


# Words that appear in almost every fact or question and would match everything
STOPWORDS = {
    "a", "an", "and", "the", "of", "in", "on", "for", "to", "with", "is", "are", "vs", "or", "how", "much",
    "what", "does", "do", "it", "my", "i", "me", "about", "can", "use", "using", "energy", "saving", "savings",
    "save", "gain", "gains", "efficient", "efficiency", "green", "code", "coding", "better", "than", "less", "more",
}


def stem(word):
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    return word


def tokenize(text):
    return {stem(word) for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 1 and word not in STOPWORDS}


# A query word matches when it equals a fact word or one is a prefix of the
# other, so "postgres" finds "postgresql" and "cache" finds "cached"
def word_matches(query_word, fact_tokens):
    if query_word in fact_tokens:
        return True
    if len(query_word) < 4:
        return False
    return any(len(token) >= 4 and (token.startswith(query_word) or query_word.startswith(token)) for token in fact_tokens)


def match_score(query_tokens, lookup):
    return sum(1 for word in query_tokens if word_matches(word, lookup["tokens"]))


# A fact starts with "- **F-ID**" and its indented continuation lines belong
# to it; "## " headings name the section.
def parse_measured_facts_markdown(path):
    facts = {}
    fact = None
    section = ""
    with open(path, encoding="utf-8") as file:
        for line in file:
            line = line.rstrip()
            if line.startswith("## "):
                section = line[3:]
                continue
            match = re.match(r"- \*\*(F-[A-Z0-9-]+)\*\*", line)
            if match:
                fact = {"id": match.group(1), "section": section, "text": line[2:]}
                facts[fact["id"]] = fact
            elif fact and line.startswith("  ") and line.strip():
                fact["text"] += "\n" + line.strip()
    return facts


# Stored facts are the fallback when no fresh value can be fetched
STORED_FACTS = parse_measured_facts_markdown(MEASURED_FACTS_FILE)

with open(FACT_LOOKUP_FILE, encoding="utf-8") as lookup_file:
    FACT_LOOKUP = json.load(lookup_file)
for lookup in FACT_LOOKUP.values():
    lookup["tokens"] = tokenize(" ".join(lookup["keywords"]))


# Fetch the newest values online

ENERGY_UNITS = {"uJ": 1e-6, "mJ": 1e-3, "J": 1}
TIME_UNITS = {"us": 1e-6, "ms": 1e-3, "s": 1}


# Reduce the GMT phase metrics ({metric: {value, unit}}) to the figures the
# facts use, with the same metric selection as data/query.sql
def summarize_metrics(phase_metrics):
    summary = {"cpu_energy_j": None, "machine_energy_j": None, "duration_s": None, "work_units": []}
    for metric, data in phase_metrics.items():
        value, unit = data["value"], data["unit"]
        if metric.startswith("cpu_energy_") and metric.endswith("_component") and unit in ENERGY_UNITS:
            summary["cpu_energy_j"] = (summary["cpu_energy_j"] or 0) + value * ENERGY_UNITS[unit]
        elif metric.startswith("psu_energy_") and metric.endswith("_machine") and unit in ENERGY_UNITS:
            summary["machine_energy_j"] = (summary["machine_energy_j"] or 0) + value * ENERGY_UNITS[unit]
        elif metric == "phase_time_syscall_system" and unit in TIME_UNITS:
            summary["duration_s"] = value * TIME_UNITS[unit]
        elif metric.startswith("custom_") and not metric.endswith("_sci_global"):
            summary["work_units"].append({"name": metric, "value": value, "unit": unit})
    return summary


# The API returns the newest successful run of every task of a software.
# Answers are kept for the session, so each software is fetched only once.
software_tasks_cache = {}
# Softwares that failed during the current search. "all" marks the API as
# unreachable, so a network problem costs one timeout per search, not per task.
failed_softwares = set()


def fetch_software_tasks(software_id):
    if software_id not in software_tasks_cache:
        request = urllib.request.Request(f"{GMT_API}/v1/software/{software_id}/tasks")
        request.add_header("Accept", "application/json")
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
        # 204 without a body: the software has no tasks
        tasks = json.loads(body)["data"] if body else []
        software_tasks_cache[software_id] = {task["id"]: task for task in tasks}
    return software_tasks_cache[software_id]


# Returns the fresh task from the API, or None if there is no newer value
def fetch_fresh_task(task_id, software_id):
    if software_id in failed_softwares or "all" in failed_softwares:
        return None
    try:
        task = fetch_software_tasks(software_id).get(task_id)
    except (urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
        print(f"[GMT API: software {software_id} could not be fetched ({e}), using the stored fact]")
        failed_softwares.add(software_id)
        return None
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"[GMT API not reachable ({e}), using the stored facts]")
        failed_softwares.add("all")
        return None
    if not task or not task.get("run_id"):
        return None
    summary = summarize_metrics(task.get("phase_metrics", {}))
    if summary["cpu_energy_j"] is None and summary["machine_energy_j"] is None:
        return None
    return task, summary


def format_number(value):
    # 3 significant digits without exponent notation: 0.273, 31.9, 1,390
    return f"{value:,.0f}" if abs(value) >= 100 else f"{value:.3g}"


def format_fresh_task(task, summary):
    figures = []
    if summary["cpu_energy_j"] is not None:
        figures.append(f"CPU energy {format_number(summary['cpu_energy_j'])} J")
    if summary["machine_energy_j"] is not None:
        figures.append(f"machine energy {format_number(summary['machine_energy_j'])} J")
    if summary["duration_s"] is not None:
        figures.append(f"duration {format_number(summary['duration_s'])} s")
    for unit in summary["work_units"]:
        figures.append(f"{unit['value']:,} {unit['unit']}")
    link = GMT_RUN_LINK.format(run_id=task["run_id"])
    return f"- {task['name']} (phase {task['phase']}): " + ", ".join(figures) + f"; run of {task['run_created_at'][:10]}: {link}"


# Fresh values where the API has them. If any task has no fresh value, the
# stored fact from measured-facts.md is used for the rest.
def describe_fact(fact_id):
    stored = STORED_FACTS[fact_id]
    lines = []
    missing = 0
    machine = None
    for lookup_task in FACT_LOOKUP[fact_id]["tasks"]:
        fresh = fetch_fresh_task(lookup_task["id"], lookup_task["software_id"])
        if fresh is None:
            missing += 1
            continue
        task, summary = fresh
        if task["machine_name"] != machine:
            machine = task["machine_name"]
            lines.append(f"On {machine}:")
        lines.append(format_fresh_task(task, summary))

    text = f"[{stored['section']}] {fact_id}"
    if lines:
        text += "\nNewest measurements from the Green Metrics Tool API:\n" + "\n".join(lines)
    if missing:
        text += "\nStored measurement from measured-facts.md:\n" + stored["text"]
    return text


def search_green_measurements(query):
    failed_softwares.clear()
    query_id = query.strip().upper()
    if query_id in FACT_LOOKUP:
        return describe_fact(query_id)

    query_tokens = tokenize(query)
    scored = sorted(
        ((match_score(query_tokens, lookup), fact_id) for fact_id, lookup in FACT_LOOKUP.items()),
        key=lambda item: item[0],
        reverse=True
    )
    best_score = scored[0][0] if scored else 0

    if best_score == 0:
        overview = "\n".join(f"- {fact_id}: {', '.join(lookup['keywords'][:4])}" for fact_id, lookup in FACT_LOOKUP.items())
        return (
            f"No measurement matches '{query}'. Available measurements (call again with an ID or other keywords):\n"
            f"{overview}"
        )

    # Only keep facts that match at least two thirds as many words as the best one
    results = [fact_id for score, fact_id in scored if score * 3 >= best_score * 2][:MAX_FACT_RESULTS]
    return "\n\n".join(describe_fact(fact_id) for fact_id in results)
