
import ollama
import json
import os
import re
import urllib.error
import urllib.request

MODEL = "gemma4:12b-mlx"

GITHUB_API = "https://api.github.com"
# Optional: set GITHUB_TOKEN for private repos and a higher rate limit
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
# Large diffs would overflow the model's context window, so they get truncated
MAX_DIFF_CHARS = 20000

# Green Metrics Tool measurements of green coding techniques. This is the
# original file, skill-references/measured-facts.md is only a copy of it.
MEASURED_FACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset", "spec", "measured-facts.md")
MAX_FACT_RESULTS = 3

SYSTEM_PROMPT = (
    "You are a green coding assistant. When the user asks about the energy use, energy saving or efficiency "
    "of a coding technique, call search_green_measurements and base your answer only on the measured figures "
    "it returns. Quote the figures with their condition, mention that they come from Green Metrics Tool "
    "micro-benchmarks and add the measurement link. If no measurement fits, say so instead of guessing."
)

tools = [
    {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_pull_request",
            "description": "Fetch a GitHub pull request including its description, diff and all comments, so it can be reviewed",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Owner (user or organization) of the repository, e.g. 'green-coding-solutions'"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name, e.g. 'green-metrics-tool'"
                    },
                    "pr_number": {
                        "type": "integer",
                        "description": "Number of the pull request"
                    }
                },
                "required": ["owner", "repo", "pr_number"]
            }
        }
    }
]


# Tool implementations

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


def match_score(query_tokens, fact):
    return sum(1 for word in query_tokens if word_matches(word, fact["tokens"]))


# Parse the facts once at startup. A fact starts with "- **F-ID**" and its
# indented continuation lines belong to it; "## " headings name the section.
def load_measured_facts(path):
    facts = []
    section = ""
    with open(path, encoding="utf-8") as file:
        for line in file:
            line = line.rstrip()
            if line.startswith("## "):
                section = line[3:]
                continue
            match = re.match(r"- \*\*(F-[A-Z0-9-]+)\*\*", line)
            if match:
                facts.append({"id": match.group(1), "section": section, "text": line[2:]})
            elif facts and line.startswith("  ") and line.strip():
                facts[-1]["text"] += "\n" + line.strip()
    for fact in facts:
        fact["tokens"] = tokenize(f"{fact['id']} {fact['section']} {fact['text']}")
    return facts


MEASURED_FACTS = load_measured_facts(MEASURED_FACTS_FILE)


def format_fact(fact):
    return f"[{fact['section']}]\n{fact['text']}"


def search_green_measurements(query):
    query_id = query.strip().upper()
    for fact in MEASURED_FACTS:
        if fact["id"] == query_id:
            return format_fact(fact)

    query_tokens = tokenize(query)
    scored = sorted(
        ((match_score(query_tokens, fact), fact) for fact in MEASURED_FACTS),
        key=lambda item: item[0],
        reverse=True
    )
    best_score = scored[0][0] if scored else 0

    if best_score == 0:
        overview = "\n".join(f"- {fact['id']} ({fact['section']})" for fact in MEASURED_FACTS)
        return (
            f"No measurement matches '{query}'. Available measurements (call again with an ID or other keywords):\n"
            f"{overview}"
        )

    # Only keep facts that match at least two thirds as many words as the best one
    results = [fact for score, fact in scored if score * 3 >= best_score * 2][:MAX_FACT_RESULTS]
    return "\n\n".join(format_fact(fact) for fact in results)


def github_request(path, accept="application/vnd.github+json"):
    request = urllib.request.Request(f"{GITHUB_API}{path}")
    request.add_header("Accept", accept)
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if GITHUB_TOKEN:
        request.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


# Dynamic: fetches the PR from the GitHub API and returns everything the
# model needs for a review as one text block
def get_pull_request(owner, repo, pr_number):
    base = f"/repos/{owner}/{repo}"
    pr_number = int(pr_number)

    try:
        pr = json.loads(github_request(f"{base}/pulls/{pr_number}"))
        diff = github_request(f"{base}/pulls/{pr_number}", accept="application/vnd.github.diff")
        # Conversation comments on the PR
        issue_comments = json.loads(github_request(f"{base}/issues/{pr_number}/comments?per_page=100"))
        # Inline comments on specific lines of the diff
        review_comments = json.loads(github_request(f"{base}/pulls/{pr_number}/comments?per_page=100"))
    except urllib.error.HTTPError as e:
        return f"GitHub API error {e.code} for {owner}/{repo}#{pr_number}: {e.reason}"
    except urllib.error.URLError as e:
        return f"Could not reach GitHub API: {e.reason}"

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + f"\n\n[... diff truncated, {len(diff) - MAX_DIFF_CHARS} more characters ...]"

    lines = [
        f"Pull request {owner}/{repo}#{pr_number}: {pr['title']}",
        f"Author: {pr['user']['login']}",
        f"State: {pr['state']}{' (merged)' if pr.get('merged') else ''}",
        f"Branch: {pr['head']['ref']} -> {pr['base']['ref']}",
        f"Changes: {pr['changed_files']} files, +{pr['additions']} -{pr['deletions']}",
        "",
        "Description:",
        pr.get("body") or "(no description)",
        "",
        "Diff:",
        diff,
        "",
        f"Comments ({len(issue_comments)}):",
    ]
    for comment in issue_comments:
        lines.append(f"- {comment['user']['login']}: {comment['body']}")

    lines += ["", f"Review comments on code lines ({len(review_comments)}):"]
    for comment in review_comments:
        lines.append(f"- {comment['user']['login']} on {comment['path']}: {comment['body']}")

    return "\n".join(lines)


# Tool registry
available_functions = {
    "search_green_measurements": search_green_measurements,
    "get_pull_request": get_pull_request,
}

# Some models (e.g. qwen2.5-coder) do not return structured tool_calls but
# write the call as JSON into the content, optionally wrapped in ```json fences
# or <tool_call> tags. Parse those so the tool actually gets executed.
def parse_tool_calls_from_content(content):
    if not content:
        return []

    candidates = re.findall(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
    candidates += re.findall(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
    if not candidates:
        candidates = [content]

    calls = []
    for candidate in candidates:
        try:
            data = json.loads(candidate.strip())
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("name") in available_functions:
                arguments = item.get("arguments", item.get("parameters", {}))
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                calls.append(ollama.Message.ToolCall(
                    function=ollama.Message.ToolCall.Function(name=item["name"], arguments=arguments)
                ))
    return calls


# Execute tool calls
def execute_tool(tool_call):
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    print(f"\n[Tool call: {name}({arguments})]")

    if name not in available_functions:
        result = f"Error: Unknown tool '{name}'"
    else:
        try:
            result = str(available_functions[name](**arguments))
        except Exception as e:
            result = f"Tool execution error: {e}"

    print(f"[Tool result: {result}]\n")
    return result


# Conversation state
messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# Main REPL loop
print(f"Chat started with {MODEL}")
print("Commands: /clear, /exit\n")

while True:
    user_input = input("You: ").strip()

    if not user_input:
        continue

    if user_input == "/exit":
        print("Goodbye!")
        break

    if user_input == "/clear":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("Conversation cleared.\n")
        continue

    # Add user message to conversation
    messages.append({
        "role": "user",
        "content": user_input
    })

    # LLM inference loop
    while True:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
            stream=True
        )

        # Print tokens as they arrive and accumulate the full message
        content = ""
        streamed_tool_calls = []
        print("\nAssistant: ", end="", flush=True)
        for chunk in stream:
            if chunk.message.content:
                print(chunk.message.content, end="", flush=True)
                content += chunk.message.content
            if chunk.message.tool_calls:
                streamed_tool_calls.extend(chunk.message.tool_calls)
        print("\n")

        assistant_message = ollama.Message(
            role="assistant",
            content=content,
            tool_calls=streamed_tool_calls or None
        )

        tool_calls = assistant_message.tool_calls or parse_tool_calls_from_content(assistant_message.content)

        # Preserve the assistant message, including (possibly parsed) tool calls
        if tool_calls and not assistant_message.tool_calls:
            assistant_message.tool_calls = tool_calls
            assistant_message.content = ""
        messages.append(assistant_message)

        # Check whether the model requested a tool
        if not tool_calls:
            break

        # Execute all requested tools
        for tool_call in tool_calls:
            result = execute_tool(tool_call)

            # Append tool result to conversation
            messages.append({
                "role": "tool",
                "tool_name": tool_call.function.name,
                "content": result
            })

        # Loop continues: model is called again with tool results
