"""Sends N GET requests over one keep-alive connection and emits the GMT custom metric http_requests.

Usage: python request-health.py --host gcb-app --port 8000 --path /health --requests 2000
"""
import argparse
import http.client
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/health")
    parser.add_argument("--requests", type=int, default=2000)
    args = parser.parse_args()

    conn = http.client.HTTPConnection(args.host, args.port, timeout=30)
    for _ in range(args.requests):
        conn.request("GET", args.path)
        resp = conn.getresponse()
        resp.read()
        if resp.status != 200:
            raise SystemExit(f"HTTP {resp.status}")
    conn.close()
    print(f"{time.time_ns()} http_requests={args.requests}")


if __name__ == "__main__":
    main()
