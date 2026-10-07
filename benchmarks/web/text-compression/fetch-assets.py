"""HTTP client for the text-compression benchmark.

Fetches the shop assets over one keep-alive connection like a browser would: sends Accept-Encoding: gzip and
decompresses gzip responses. Emits GMT custom metrics for requests and bytes transferred on the wire.

Usage: python fetch-assets.py --host gcb-shop-nginx --rounds 500
"""
import argparse
import gzip
import http.client
import time

ASSETS = ["/index.html", "/app.js", "/style.css", "/data/products.json"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--rounds", type=int, default=500)
    args = parser.parse_args()

    conn = http.client.HTTPConnection(args.host, args.port, timeout=30)
    wire_bytes = 0
    requests = 0
    for _ in range(args.rounds):
        for path in ASSETS:
            conn.request("GET", path, headers={"Accept-Encoding": "gzip"})
            resp = conn.getresponse()
            body = resp.read()
            if resp.status != 200:
                raise SystemExit(f"{path}: HTTP {resp.status}")
            wire_bytes += len(body)
            if resp.getheader("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            requests += 1
    conn.close()

    ts = time.time_ns()
    print(f"{ts} http_requests={requests}")
    print(f"{ts} transferred_kb={wire_bytes // 1024}")


if __name__ == "__main__":
    main()
