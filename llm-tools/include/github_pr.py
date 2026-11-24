"""GitHub PR tool: fetches a pull request with its diff and comments so the
model can review it."""

import json
import os
import urllib.error
import urllib.request

GITHUB_API = "https://api.github.com"
# Optional: set GITHUB_TOKEN for private repos and a higher rate limit
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
# Large diffs would overflow the model's context window, so they get truncated
MAX_DIFF_CHARS = 20000

TOOL = {
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
