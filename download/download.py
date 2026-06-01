#!/usr/bin/env python3
import sys
import requests

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url>")
        sys.exit(1)

    url = sys.argv[1]

    r = requests.get(url, stream=True)
    r.raise_for_status()

    out_path = "/dev/null"
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
