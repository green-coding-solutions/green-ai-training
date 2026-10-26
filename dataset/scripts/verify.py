#!/usr/bin/env python3
"""Verifies example sources in ../examples and writes ../out/verify-report.json.

Checks per example:
  schema        ids, categories, patterns, message order
  style         Green Notes / review format per category, code fence tags, banned phrases, spec leakage
  numbers       energy / % / multiplier figures only when backed by a cited fact in spec/measured-facts.md
  urls          no pattern catalog, measurement or benchmark links in answers, only the figures themselves
  scope         language must be benchmarked for the example's patterns, at least one backing fact
  syntax        python (ast), javascript (node --check), bash (bash -n), json, yaml, sql (sqlite parser)
  execution     optional `verify:` block -> run, test, equivalence (original vs green output), benchmark (CPU time)
  contamination code in user messages must not be a near copy of ../../test-cases (that is the eval set)
  duplicates    near-duplicate user prompts across the dataset

Usage:
  python scripts/verify.py                    # all examples
  python scripts/verify.py examples/python    # a subset
  python scripts/verify.py --no-exec          # skip running code
"""

import argparse
import ast
import hashlib
import json
import os
import re
import resource
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from common import (OUT_DIR, SPEC_DIR, TEST_CASES_DIR, extract_code_blocks, jaccard, load_examples, load_taxonomy,
                    shingles, strip_code_blocks)

# cache entries are invalidated whenever this file or the spec changes
VERIFIER_VERSION = hashlib.sha256(b"".join(f.read_bytes() for f in [Path(__file__), SPEC_DIR / "measured-facts.md", SPEC_DIR / "taxonomy.yaml"])).hexdigest()

ALLOWED_LANGS = {
    "python", "javascript", "typescript", "sql", "bash", "sh", "html", "css", "go", "java", "rust", "yaml",
    "dockerfile", "json", "text", "toml", "ini", "diff", "nginx", "xml", "jsx", "tsx", "console",
}
LANG_ALIASES = {"py": "python", "js": "javascript", "ts": "typescript", "shell": "bash", "yml": "yaml", "sh": "bash"}
SEVERITY_RE = re.compile(r"^#### \[(High|Medium|Low|Bug|Security)\]", re.MULTILINE)
BANNED_PHRASES = ["as an ai", "i hope this helps", "great question", "happy coding", "certainly!", "i'd be happy to"]
SPEC_LEAK_RE = re.compile(r"(?-i:\bF-[A-Z]{2,}(?:-[A-Z]+)*\b)|house rules|measured-facts|taxonomy\.yaml|teacher model", re.IGNORECASE)
GREEN_WORDS_RE = re.compile(r"\b(green|carbon|co2|sustainab\w*|emission\w*|SCI)\b", re.IGNORECASE)

NUM = r"(\d[\d,]*(?:\.\d+)?)"
NUMBER_PATTERNS = [
    re.compile(NUM + r"\s*(?:mWh|kWh|Wh|kJ|J|joules?|g ?CO2e?|kg ?CO2e?)\b"),
    re.compile(NUM + r"\s*%"),
    re.compile(r"(?:about|roughly|around|~|up to|over|nearly|almost|approximately)\s*" + NUM + r"\s*[×x](?![\w/])",
               re.IGNORECASE),
    re.compile(NUM + r"\s*[×x]\s+(?:\w+\s+){0,2}?(?:less|more|faster|slower|cheaper|smaller|larger|bigger|lower|higher"
               r"|fewer|speedup|reduction)\b", re.IGNORECASE),
    re.compile(NUM + r"\s*times\s+(?:less|more|faster|slower|cheaper)", re.IGNORECASE),
]

REFERENCE_URL_RE = re.compile(r"https?://(?:patterns\.greensoftware\.foundation|metrics\.green-coding\.io|github\.com/green-coding-solutions)[^\s)>\]`\"']*")
URL_RE = re.compile(r"https?://[^\s)>\]`\"']+")

EXEC_TIMEOUT = 60


# ---------------------------------------------------------------- helpers

def norm_lang(lang):
    return LANG_ALIASES.get(lang, lang)


def assistant_turns(ex):
    return [m for m in ex.get("messages", []) if m.get("role") == "assistant"]


def user_turns(ex):
    return [m for m in ex.get("messages", []) if m.get("role") == "user"]


def load_facts():
    facts = {}
    text = (SPEC_DIR / "measured-facts.md").read_text(encoding="utf-8")
    for block in re.split(r"\n(?=- \*\*F-)", text):
        m = re.match(r"- \*\*(F-[A-Z-]+)\*\*", block)
        if m:
            facts[m.group(1)] = block
    return facts


def normalize_number(s):
    return s.replace(",", "")


def run_process(cmd, code, timeout=EXEC_TIMEOUT, suffix=".py", files=None):
    """Runs code from a temp file. Returns (returncode, stdout, stderr, cpu_seconds)."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, content in (files or {}).items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                f.write(content)
        path = os.path.join(tmp, "snippet" + suffix)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        try:
            proc = subprocess.run(cmd + [path], cwd=tmp, capture_output=True, text=True, timeout=timeout,
                                  env={"PATH": os.environ.get("PATH", ""), "HOME": tmp, "PYTHONHASHSEED": "0",
                                       "LANG": "C.UTF-8"})
        except subprocess.TimeoutExpired:
            return -1, "", f"timeout after {timeout}s", None
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
        return proc.returncode, proc.stdout, proc.stderr, cpu


RUNTIMES = {
    "python": ([sys.executable], ".py"),
    "javascript": (["node"], ".mjs"),
    "bash": (["bash"], ".sh"),
}


# ---------------------------------------------------------------- checks

def check_schema(ex, taxonomy, errors, warnings):
    for key in ("id", "category", "messages"):
        if key not in ex:
            errors.append(f"schema: missing '{key}'")
    if ex.get("category") not in taxonomy["categories"]:
        errors.append(f"schema: unknown category {ex.get('category')!r}")
    known = {p["id"] for p in taxonomy["patterns"]}
    for p in ex.get("patterns", []) or []:
        if p not in known:
            errors.append(f"schema: unknown pattern {p!r}")
    if not ex.get("patterns"):
        warnings.append("schema: no patterns listed")
    msgs = ex.get("messages") or []
    if not msgs:
        return
    for i, m in enumerate(msgs):
        expected = "user" if i % 2 == 0 else "assistant"
        if m.get("role") != expected:
            errors.append(f"schema: message {i} should be role {expected}, got {m.get('role')!r}")
        if not isinstance(m.get("content"), str) or not m["content"].strip():
            errors.append(f"schema: message {i} has empty content")
    if msgs[-1].get("role") != "assistant":
        errors.append("schema: conversation must end with an assistant message")
    if ex.get("category") == "multi-turn" and len(msgs) < 4:
        errors.append("schema: multi-turn needs at least 2 user turns")


def check_scope(ex, taxonomy, errors):
    # the dataset only teaches what the benchmarks measured: their languages and their facts
    by_id = {p["id"]: p for p in taxonomy["patterns"]}
    category, language = ex.get("category"), ex.get("language")
    measured = [by_id[p] for p in ex.get("patterns") or [] if p in by_id and by_id[p]["languages"]]
    if category != "conceptual":
        for p in measured:
            if language not in p["languages"]:
                errors.append(f"scope: pattern {p['id']} was only benchmarked in {p['languages']}, not {language!r}")
    cited = set(ex.get("facts") or [])
    if not cited:
        errors.append("scope: no facts cited, every example needs a measured fact")
    elif measured and not cited & {f for p in measured for f in p.get("facts") or []}:
        errors.append(f"scope: cited facts {sorted(cited)} do not back any of the patterns {[p['id'] for p in measured]}")


def check_style(ex, errors, warnings):
    category = ex.get("category")
    assistants = assistant_turns(ex)
    if not assistants:
        return
    final = assistants[-1]["content"]
    all_user = "\n".join(m["content"] for m in user_turns(ex))

    for m in ex.get("messages", []):
        for block in extract_code_blocks(m["content"]):
            if block.code is None:
                errors.append(f"style: unterminated code fence in {m['role']} message")
            elif m["role"] == "assistant" and not block.lang:
                errors.append("style: assistant code block without language tag")
            elif block.lang and norm_lang(block.lang) not in ALLOWED_LANGS:
                warnings.append(f"style: unusual code block language {block.lang!r}")

    for m in assistants:
        low = m["content"].lower()
        for phrase in BANNED_PHRASES:
            if phrase in low:
                errors.append(f"style: banned phrase {phrase!r}")
        if SPEC_LEAK_RE.search(strip_code_blocks(m["content"])):
            errors.append(f"style: spec leakage {SPEC_LEAK_RE.search(m['content']).group(0)!r}")

    has_notes = "**Green Notes**" in final
    if category in ("generation", "refactor") and not has_notes:
        errors.append(f"style: {category} answer must contain '**Green Notes**'")
    if category == "review" and not (SEVERITY_RE.search(final) or "No efficiency issues" in final):
        errors.append("style: review must contain '#### [High|Medium|Low|Bug|Security]' findings "
                      "or 'No efficiency issues'")
    if category == "no-change" and re.search(r"^#### \[(High|Medium)\]", final, re.MULTILINE):
        errors.append("style: no-change answer must not contain High/Medium findings")
    if category == "general":
        if has_notes:
            errors.append("style: general answer must not contain Green Notes")
        prose = strip_code_blocks(final)
        if GREEN_WORDS_RE.search(prose) and not GREEN_WORDS_RE.search(all_user):
            errors.append(f"style: general answer lectures about sustainability "
                          f"({GREEN_WORDS_RE.search(prose).group(0)!r}) although user did not ask")

    words = len(final.split())
    if words > 900:
        warnings.append(f"style: final answer is long ({words} words)")


def check_numbers(ex, facts, errors):
    cited = ex.get("facts") or []
    for fid in cited:
        if fid not in facts:
            errors.append(f"numbers: unknown fact id {fid!r}")
    # digits inside run ids and links are not figures
    allowed_text = normalize_number(URL_RE.sub("", " ".join(facts.get(f, "") for f in cited)))
    allowed_numbers = set(re.findall(r"\d+(?:\.\d+)?", allowed_text))
    # repeating a figure the user gave (e.g. "~40% of values are missing") is not fabrication
    user_text = normalize_number(" ".join(m["content"] for m in user_turns(ex)))
    allowed_numbers |= set(re.findall(r"\d+(?:\.\d+)?", user_text))
    for m in assistant_turns(ex):
        prose = strip_code_blocks(m["content"])
        prose = re.sub(r"`[^`\n]*`", "", prose)  # inline code
        prose = URL_RE.sub("", prose)
        for pattern in NUMBER_PATTERNS:
            for hit in pattern.finditer(prose):
                number = normalize_number(hit.group(1))
                if number not in allowed_numbers:
                    errors.append(f"numbers: unbacked figure {hit.group(0)!r} (cite a fact in 'facts:' or rephrase)")


STAR_IMPORT_RE = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+\*", re.MULTILINE)


def check_star_imports(ex, errors):
    """Changing star imports is an anti-pattern (no measurable energy difference, F-IMPORT): answers must keep them."""
    user_code = "\n".join(b.code or "" for m in user_turns(ex) for b in extract_code_blocks(m["content"])
                          if norm_lang(b.lang) == "python")
    star_modules = set(STAR_IMPORT_RE.findall(user_code))
    if not star_modules:
        return
    for m in assistant_turns(ex):
        for b in extract_code_blocks(m["content"]):
            if norm_lang(b.lang) != "python" or not b.code:
                continue
            kept = set(STAR_IMPORT_RE.findall(b.code))
            for mod in star_modules - kept:
                if re.search(rf"^\s*(?:import\s+{re.escape(mod)}\b|from\s+{re.escape(mod)}\s+import\b)", b.code, re.M):
                    errors.append(f"style: star import of {mod!r} was converted. Leave star imports unchanged")


def bash_literal_double_quotes(code):
    """Returns double-quoted strings without anything to expand (should be single-quoted)."""
    found = []
    for line in code.splitlines():
        if line.lstrip().startswith("#"):
            continue
        i, n = 0, len(line)
        while i < n:
            c = line[i]
            if c == "\\":
                i += 2
                continue
            if c == "'":
                j = line.find("'", i + 1)
                i = n if j == -1 else j + 1
                continue
            if c == "#" and (i == 0 or line[i - 1] in " \t;"):
                break
            if c == '"':
                j, depth, content = i + 1, 0, []
                while j < n:
                    d = line[j]
                    if d == "\\":
                        content.append(line[j:j + 2]); j += 2; continue
                    if d == "$" and j + 1 < n and line[j + 1] == "(":
                        depth += 1
                    elif d == ")" and depth:
                        depth -= 1
                    elif d == '"' and depth == 0:
                        break
                    content.append(d); j += 1
                text = "".join(content)
                if text and not any(ch in text for ch in "$`\\'!"):
                    found.append(text)
                i = j + 1
                continue
            i += 1
    return found


def check_bash_quoting(ex, errors):
    for m in assistant_turns(ex):
        for b in extract_code_blocks(m["content"]):
            if norm_lang(b.lang) == "bash" and b.code:
                lits = bash_literal_double_quotes(b.code)
                if lits:
                    errors.append(f"style: bash literal(s) in double quotes, use single quotes: {lits[:3]}")


def check_urls(ex, errors):
    # reference links teach the model to reproduce run ids it cannot know, only the figures are kept
    for m in assistant_turns(ex):
        for url in REFERENCE_URL_RE.findall(m["content"]):
            errors.append(f"urls: reference link in answer, quote the figure without a link: {url.rstrip('.,;:')}")


def sqlite_syntax_error(sql):
    con = sqlite3.connect(":memory:")
    try:
        for stmt in split_sql(sql):
            try:
                con.execute("EXPLAIN " + stmt)
            except sqlite3.OperationalError as e:
                msg = str(e)
                if "syntax error" in msg or "incomplete input" in msg or "unrecognized token" in msg:
                    return f"{msg} in: {stmt[:80]!r}"
    finally:
        con.close()
    return None


def split_sql(sql):
    stmts, buf = [], ""
    for line in sql.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                stmts.append(buf.strip())
            buf = ""
    if buf.strip():
        stmts.append(buf.strip())
    return stmts


def check_syntax(ex, errors, warnings, verified):
    dialect = ex.get("sql_dialect", "sqlite")
    checked = 0
    for m in ex.get("messages", []):
        # user code may intentionally be broken in debugging conversations
        if m["role"] == "user" and not ex.get("check_user_code", True):
            continue
        for block in extract_code_blocks(m["content"]):
            if block.code is None:
                continue
            lang = norm_lang(block.lang)
            code = block.code
            where = f"{m['role']} {lang}"
            if lang == "python":
                try:
                    ast.parse(code)
                    checked += 1
                except SyntaxError as e:
                    (errors if m["role"] == "assistant" else warnings).append(
                        f"syntax: {where}: {e.msg} (line {e.lineno})")
            elif lang == "javascript":
                rc, _, err, _ = run_process(["node", "--check"], code, timeout=20, suffix=".mjs")
                if rc != 0:
                    rc2, _, err2, _ = run_process(["node", "--check"], code, timeout=20, suffix=".cjs")
                    if rc2 != 0:
                        (errors if m["role"] == "assistant" else warnings).append(
                            f"syntax: {where}: {(err or err2).strip().splitlines()[-1] if (err or err2) else 'error'}")
                        continue
                checked += 1
            elif lang == "bash":
                rc, _, err, _ = run_process(["bash", "-n"], code, timeout=20, suffix=".sh")
                if rc != 0:
                    (errors if m["role"] == "assistant" else warnings).append(f"syntax: {where}: {err.strip()}")
                else:
                    checked += 1
            elif lang == "json":
                try:
                    json.loads(code)
                    checked += 1
                except json.JSONDecodeError as e:
                    (errors if m["role"] == "assistant" else warnings).append(f"syntax: {where}: {e}")
            elif lang == "yaml":
                try:
                    list(yaml.safe_load_all(code))
                    checked += 1
                except yaml.YAMLError as e:
                    (errors if m["role"] == "assistant" else warnings).append(
                        f"syntax: {where}: {str(e).splitlines()[0]}")
            elif lang == "sql" and dialect == "sqlite":
                err = sqlite_syntax_error(code)
                if err:
                    (errors if m["role"] == "assistant" else warnings).append(f"syntax: {where}: {err}")
                else:
                    checked += 1
    if checked:
        verified.append("syntax")


def select_blocks(ex, lang):
    v = ex.get("verify") or {}
    lang = norm_lang(lang)
    final_blocks = [b for b in extract_code_blocks(assistant_turns(ex)[-1]["content"]) if norm_lang(b.lang) == lang]
    green = v.get("green_code")
    if green is None and final_blocks:
        i = v.get("green_block", -1)
        green = final_blocks[i].code if -len(final_blocks) <= i < len(final_blocks) else None
    original = v.get("original_code")
    if original is None:
        first_user_blocks = [b for b in extract_code_blocks(user_turns(ex)[0]["content"]) if norm_lang(b.lang) == lang]
        i = v.get("original_block", 0)
        if -len(first_user_blocks) <= i < len(first_user_blocks):
            original = first_user_blocks[i].code
    return original, green


def check_execution(ex, errors, verified, metrics):
    v = ex.get("verify")
    if not v:
        return
    if v.get("static_only"):
        verified.append("static-only")
        return
    if "sql" in v:
        return check_sql(ex, v["sql"], errors, verified)

    lang = norm_lang(v.get("lang", ex.get("language", "python")))
    if lang not in RUNTIMES:
        errors.append(f"exec: no runtime for language {lang!r}")
        return
    cmd, suffix = RUNTIMES[lang]
    original, green = select_blocks(ex, lang)
    if green is None:
        errors.append(f"exec: no {lang} code block found in final assistant message")
        return
    setup = v.get("setup", "")
    timeout = v.get("timeout", EXEC_TIMEOUT)

    def run(code, extra=""):
        if v.get("module") and lang == "python":
            # code is imported as solution.py, so `if __name__ == "__main__":` blocks don't run
            solution = "\n".join(p for p in (setup, code) if p)
            return run_process(cmd, "from solution import *\n" + extra, timeout=timeout, suffix=suffix,
                               files={"solution.py": solution})
        return run_process(cmd, "\n".join(p for p in (setup, code, extra) if p), timeout=timeout, suffix=suffix)

    if v.get("run"):
        rc, out, err, _ = run(green)
        if rc != 0:
            errors.append(f"exec: green code failed (rc={rc}): {err.strip()[-300:]}")
        else:
            verified.append("run")
    if v.get("test"):
        rc, out, err, _ = run(green, v["test"])
        if rc != 0:
            errors.append(f"exec: test failed (rc={rc}): {err.strip()[-300:]}")
        else:
            verified.append("test")
    if v.get("equivalence"):
        if original is None:
            errors.append("exec: equivalence needs original code (user code block or verify.original_code)")
        else:
            driver = v["equivalence"].get("driver", "") if isinstance(v["equivalence"], dict) else ""
            rc1, out1, err1, _ = run(original, driver)
            rc2, out2, err2, _ = run(green, driver)
            if rc1 != 0:
                errors.append(f"exec: original failed in equivalence run: {err1.strip()[-300:]}")
            elif rc2 != 0:
                errors.append(f"exec: green failed in equivalence run: {err2.strip()[-300:]}")
            elif out1.strip() != out2.strip():
                errors.append(f"exec: output differs. original={out1.strip()[:200]!r} green={out2.strip()[:200]!r}")
            else:
                verified.append("equivalence")
    if v.get("benchmark"):
        b = v["benchmark"]
        if original is None:
            errors.append("exec: benchmark needs original code")
            return
        driver = b.get("driver", "")
        repeats = b.get("repeats", 3)
        cpu_o, cpu_g = [], []
        for _ in range(repeats):
            rc1, out1, err1, c1 = run(original, driver)
            rc2, out2, err2, c2 = run(green, driver)
            if rc1 != 0 or rc2 != 0:
                errors.append(f"exec: benchmark run failed: {(err1 or err2).strip()[-300:]}")
                return
            # drivers may time only the code under test and print "__CPU__ <seconds>"
            cpu_o.append(cpu_marker(out1, c1))
            cpu_g.append(cpu_marker(out2, c2))
        speedup = min(cpu_o) / max(min(cpu_g), 1e-6)
        metrics["cpu_original_s"] = round(min(cpu_o), 4)
        metrics["cpu_green_s"] = round(min(cpu_g), 4)
        metrics["cpu_speedup"] = round(speedup, 2)
        if speedup < b.get("min_speedup", 1.1):
            errors.append(f"exec: green version not measurably cheaper (CPU speedup {speedup:.2f}x, "
                          f"need {b.get('min_speedup', 1.1)}x)")
        else:
            verified.append("benchmark")


def cpu_marker(stdout, fallback):
    m = re.findall(r"__CPU__\s+([0-9.eE-]+)", stdout)
    return sum(float(x) for x in m) if m else fallback


def check_sql(ex, cfg, errors, verified):
    original, green = select_blocks(ex, "sql")
    if green is None:
        errors.append("exec: no sql block in final assistant message")
        return

    def execute(sql):
        con = sqlite3.connect(":memory:")
        try:
            con.executescript(cfg.get("setup", ""))
            rows = None
            for stmt in split_sql(sql):
                cur = con.execute(stmt)
                if cur.description:
                    rows = cur.fetchall()
            return rows
        finally:
            con.close()

    try:
        green_rows = execute(green)
    except sqlite3.Error as e:
        errors.append(f"exec: green SQL failed: {e}")
        return
    verified.append("run")
    if cfg.get("compare"):
        try:
            orig_rows = execute(original)
        except sqlite3.Error as e:
            errors.append(f"exec: original SQL failed: {e}")
            return
        key = (lambda r: r) if cfg.get("ordered") else sorted
        if key(orig_rows or []) != key(green_rows or []):
            errors.append(f"exec: SQL results differ: original={str(orig_rows)[:150]} green={str(green_rows)[:150]}")
        else:
            verified.append("equivalence")


def load_test_case_shingles():
    result = {}
    if not TEST_CASES_DIR.exists():
        return result
    for path in TEST_CASES_DIR.rglob("*"):
        if path.is_file() and (path.suffix in {".py", ".sh", ".html", ".sql", ".js", ".css", ".yml", ".yaml", ".conf",
                                               ".json", ".ts"} or path.name == "Dockerfile"):
            result[str(path.relative_to(TEST_CASES_DIR))] = shingles(path.read_text(encoding="utf-8", errors="ignore"))
    return result


def check_contamination(ex, test_shingles, errors):
    for m in user_turns(ex):
        for block in extract_code_blocks(m["content"]):
            if not block.code or len(block.code) < 80:
                continue
            s = shingles(block.code)
            for name, ts in test_shingles.items():
                score = jaccard(s, ts)
                if score >= 0.5:
                    errors.append(f"contamination: user code is {score:.0%} similar to test-cases/{name}")


def find_duplicates(entries, threshold=0.8):
    """MinHash-banded near-duplicate search on the first user message. Returns {id: duplicate_of}."""
    num_hashes, bands = 32, 8
    rows = num_hashes // bands
    sigs, sh = {}, {}
    for ex_id, text in entries:
        s = shingles(text)
        sh[ex_id] = s
        hashes = [int(hashlib.md5(x.encode()).hexdigest()[:12], 16) for x in s] or [0]
        sigs[ex_id] = [min((h ^ (i * 0x9E3779B97F4A7C15)) & 0xFFFFFFFFFFFF for h in hashes) for i in range(num_hashes)]
    buckets = defaultdict(list)
    for ex_id, sig in sigs.items():
        for b in range(bands):
            buckets[(b, tuple(sig[b * rows:(b + 1) * rows]))].append(ex_id)
    dups = {}
    order = {ex_id: i for i, (ex_id, _) in enumerate(entries)}
    for members in buckets.values():
        for i, a in enumerate(members):
            for b_id in members[i + 1:]:
                first, second = sorted((a, b_id), key=order.get)
                if second not in dups and jaccard(sh[first], sh[second]) >= threshold:
                    dups[second] = first
    return dups


# ---------------------------------------------------------------- main

def example_hash(ex):
    return hashlib.sha256((VERIFIER_VERSION + json.dumps(ex, sort_keys=True, default=str)).encode()).hexdigest()


def verify_all(paths=None, no_exec=False, use_cache=True, quiet=False):
    taxonomy = load_taxonomy()
    facts = load_facts()
    test_shingles = load_test_case_shingles()
    cache_path = OUT_DIR / "verify-cache.json"
    cache = {}
    if use_cache and cache_path.exists() and cache_path.stat().st_size:
        cache = json.loads(cache_path.read_text())

    report, seen, dedupe_entries = {}, set(), []
    for path, ex in load_examples(paths):
        ex_id = ex.get("id", f"<missing id in {path.name}>")
        h = example_hash(ex)
        if use_cache and not no_exec and h in cache:
            entry = dict(cache[h])
            entry["file"] = str(path)
        else:
            errors, warnings, verified, metrics = [], [], [], {}
            check_schema(ex, taxonomy, errors, warnings)
            if not errors:
                check_scope(ex, taxonomy, errors)
                check_style(ex, errors, warnings)
                check_numbers(ex, facts, errors)
                check_urls(ex, errors)
                check_star_imports(ex, errors)
                check_bash_quoting(ex, errors)
                check_syntax(ex, errors, warnings, verified)
                check_contamination(ex, test_shingles, errors)
                if not no_exec and not errors:
                    check_execution(ex, errors, verified, metrics)
            entry = {"file": str(path), "category": ex.get("category"), "patterns": ex.get("patterns") or [],
                     "language": ex.get("language"), "errors": errors, "warnings": warnings,
                     "verified": verified, **metrics}
            if not no_exec:
                cache[h] = {k: v for k, v in entry.items() if k != "file"}
        if ex_id in seen:
            entry = dict(entry, errors=entry["errors"] + [f"schema: duplicate id {ex_id!r}"])
        seen.add(ex_id)
        report[ex_id] = entry
        if ex.get("messages"):
            dedupe_entries.append((ex_id, ex["messages"][0].get("content", "")))
        if not quiet:
            status = "FAIL" if entry["errors"] else "ok  "
            print(f"{status} {ex_id:45s} {','.join(entry['verified'])}"
                  + (f"  speedup={entry['cpu_speedup']}x" if entry.get("cpu_speedup") else ""))
            for e in entry["errors"]:
                print(f"       ✗ {e}")
            for w in entry["warnings"]:
                print(f"       ! {w}")

    for dup, original in find_duplicates(dedupe_entries).items():
        report[dup]["errors"] = report[dup]["errors"] + [f"duplicates: first user message near-identical to {original}"]
        if not quiet:
            print(f"FAIL {dup:45s} near-duplicate of {original}")

    for entry in report.values():
        entry["status"] = "fail" if entry["errors"] else "pass"

    OUT_DIR.mkdir(exist_ok=True)
    if not no_exec:
        cache_path.write_text(json.dumps(cache, indent=1))
    return report


def summarize(report):
    taxonomy = load_taxonomy()
    passed = {k: v for k, v in report.items() if v["status"] == "pass"}
    print(f"\n{len(passed)}/{len(report)} examples pass")
    cats = Counter(v["category"] for v in passed.values())
    total = max(len(passed), 1)
    print("\nCategory mix (pass)       actual   target")
    for cat, spec in taxonomy["categories"].items():
        print(f"  {cat:22s} {cats.get(cat, 0):5d} {cats.get(cat, 0) / total:7.0%} {spec['weight']:7.0%}")
    levels = Counter(lvl for v in passed.values() for lvl in v["verified"])
    print("\nVerification levels: " + ", ".join(f"{k}={n}" for k, n in sorted(levels.items())))
    pats = Counter(p for v in passed.values() for p in v["patterns"])
    missing = [p["id"] for p in taxonomy["patterns"] if p["id"] not in pats]
    print(f"Patterns covered: {len(pats)}/{len(taxonomy['patterns'])}")
    if missing:
        print("  not covered: " + ", ".join(missing))
    langs = Counter(v.get("language") for v in passed.values())
    print("Languages: " + ", ".join(f"{k}={n}" for k, n in langs.most_common()))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="Example files or directories (default: examples/)")
    parser.add_argument("--no-exec", action="store_true", help="Skip code execution checks")
    parser.add_argument("--no-cache", action="store_true", help="Ignore the verification cache")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    report = verify_all(args.paths or None, no_exec=args.no_exec, use_cache=not args.no_cache, quiet=args.quiet)
    (OUT_DIR / "verify-report.json").write_text(json.dumps(report, indent=1))
    summarize(report)
    sys.exit(1 if any(v["status"] == "fail" for v in report.values()) else 0)


if __name__ == "__main__":
    main()
