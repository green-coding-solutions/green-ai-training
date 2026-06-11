import urllib.request
import sys

URL = "https://codetactics.de"

for _ in range(10):
    with urllib.request.urlopen(URL) as response:
        response.read()
        if response.status != 200:
            print(f"Expected HTTP 200, got {response.status}", file=sys.stderr)
            sys.exit(1)
