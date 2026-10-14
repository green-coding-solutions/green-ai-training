"""Shared helpers for the green coding dataset pipeline: loading example sources, extracting code blocks."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

DATASET_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = DATASET_DIR.parent
SPEC_DIR = DATASET_DIR / "spec"
EXAMPLES_DIR = DATASET_DIR / "examples"
OUT_DIR = DATASET_DIR / "out"
TEST_CASES_DIR = REPO_DIR / "test-cases"

FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>[^\n`]*)$", re.MULTILINE)


@dataclass
class CodeBlock:
    lang: str
    code: str


def load_taxonomy():
    with open(SPEC_DIR / "taxonomy.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_spec_text():
    """Concatenated teacher spec: GSF rules, house rules, measured facts, taxonomy."""
    parts = []
    for name in ("gsf-green-code-skill.md", "house-rules.md", "measured-facts.md", "taxonomy.yaml"):
        parts.append(f"<file name=\"{name}\">\n{(SPEC_DIR / name).read_text(encoding='utf-8')}\n</file>")
    return "\n\n".join(parts)


def iter_example_files(paths=None):
    roots = [Path(p) for p in paths] if paths else [EXAMPLES_DIR]
    for root in roots:
        if root.is_file():
            yield root
        else:
            yield from sorted(root.rglob("*.yaml"))


def load_examples(paths=None):
    """Yields (path, example_dict). A file may hold several YAML documents separated by '---'."""
    for path in iter_example_files(paths):
        with open(path, encoding="utf-8") as f:
            for doc in yaml.safe_load_all(f):
                if doc:
                    yield path, doc


def extract_code_blocks(markdown):
    """Returns fenced code blocks in order. Handles nested fences of different length."""
    blocks = []
    pos = 0
    while True:
        m = FENCE_RE.search(markdown, pos)
        if not m:
            break
        fence = m.group("fence")
        lang = m.group("info").strip().split(" ")[0].lower()
        close_re = re.compile(r"^[ \t]*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$", re.MULTILINE)
        close = close_re.search(markdown, m.end())
        if not close:
            blocks.append(CodeBlock(lang=lang, code=None))  # unterminated
            break
        code = markdown[m.end() + 1:close.start()]
        blocks.append(CodeBlock(lang=lang, code=code))
        pos = close.end()
    return blocks


def strip_code_blocks(markdown):
    out, pos = [], 0
    while True:
        m = FENCE_RE.search(markdown, pos)
        if not m:
            out.append(markdown[pos:])
            break
        out.append(markdown[pos:m.start()])
        fence = m.group("fence")
        close_re = re.compile(r"^[ \t]*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$", re.MULTILINE)
        close = close_re.search(markdown, m.end())
        if not close:
            break
        pos = close.end()
    return "".join(out)


def shingles(text, k=5):
    tokens = re.findall(r"\w+|[^\w\s]", text.lower())
    return {" ".join(tokens[i:i + k]) for i in range(max(len(tokens) - k + 1, 1))}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class _BlockDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper, data):
    if "\n" in data:
        # strip trailing spaces per line so PyYAML can use the readable block style
        data = "\n".join(line.rstrip() for line in data.split("\n"))
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_BlockDumper.add_representer(str, _str_representer)


def dump_yaml(obj):
    return yaml.dump(obj, Dumper=_BlockDumper, sort_keys=False, allow_unicode=True, width=120)
