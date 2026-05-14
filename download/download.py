#!/usr/bin/env python3
import sys
import requests

BASE_URL = "http://192.168.178.21:5000/v2/greencoding/gcb_playwright/blobs/sha256:"

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <sha256-hash>")
        sys.exit(1)

    sha = sys.argv[1]
    url = BASE_URL + sha

    r = requests.get(url, stream=True)
    r.raise_for_status()

    out_path = "/tmp/myfile"
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()