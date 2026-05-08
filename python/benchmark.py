import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request


def metric_line(metric_name, value):
    print(f"{time.time_ns()} {metric_name}={int(value)}")


def run_until(min_runtime, block):
    total_units = 0
    start = time.perf_counter()
    ran_once = False
    while not ran_once or (time.perf_counter() - start) < min_runtime:
        total_units += block()
        ran_once = True
    return total_units


def wait_http(server_url, timeout_seconds):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(server_url, timeout=2) as response:
                if response.status == 200:
                    return 0
        except Exception:
            time.sleep(0.25)
    raise TimeoutError(f"Server at {server_url} did not become healthy within {timeout_seconds}s")


def idle(seconds):
    time.sleep(seconds)
    return seconds


def empty_loop(size, min_runtime):
    def block():
        for _ in range(size):
            pass
        return size

    return run_until(min_runtime, block)


def integer_arithmetic(size, min_runtime):
    state = [1]

    def block():
        acc = state[0]
        for i in range(size):
            acc = ((acc * 3) + i + 7) % 1000003
        state[0] = acc
        return size

    return run_until(min_runtime, block)


def memory_sequential(size, min_runtime):
    buf = bytearray((i % 251 for i in range(size)))
    sink = [0]

    def block():
        checksum = sink[0]
        for index, value in enumerate(buf):
            checksum ^= value
            buf[index] = (value + 1) & 255
        sink[0] = checksum
        return size * 2

    return run_until(min_runtime, block)


def dict_lookup(size, min_runtime):
    mapping = {f"k{i}": i for i in range(size)}
    keys = list(mapping.keys())
    position = [0]
    sink = [0]

    def block():
        idx = position[0]
        total = sink[0]
        for _ in range(size):
            key = keys[idx]
            total += mapping[key]
            idx += 1
            if idx == size:
                idx = 0
        position[0] = idx
        sink[0] = total
        return size

    return run_until(min_runtime, block)


def json_roundtrip(size, min_runtime):
    payload = json.dumps(
        [
            {"id": i, "name": f"item-{i}", "active": bool(i % 2), "value": i * 3}
            for i in range(size)
        ],
        separators=(",", ":"),
    )
    sink = [0]

    def block():
        data = json.loads(payload)
        encoded = json.dumps(data, separators=(",", ":"))
        sink[0] = len(encoded)
        return len(payload) + len(encoded)

    return run_until(min_runtime, block)


def sort_items(size, min_runtime):
    base = [((size - i) * 37) % 100003 for i in range(size)]
    sink = [0]

    def block():
        values = list(base)
        values.sort()
        sink[0] = values[0] if values else 0
        return size

    return run_until(min_runtime, block)


def subprocess_spawn(size, min_runtime):
    def block():
        for _ in range(size):
            subprocess.run(["/bin/true"], check=True)
        return size

    return run_until(min_runtime, block)


def http_requests(size, min_runtime, server_url):
    def block():
        for _ in range(size):
            with urllib.request.urlopen(f"{server_url}/json", timeout=5) as response:
                response.read()
        return size

    return run_until(min_runtime, block)


def page_assets(size, min_runtime, server_url, image_bytes):
    img_pattern = re.compile(r'<img[^>]+src="([^"]+)"')

    def fetch(url):
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read()

    page_url = f"{server_url}/page?images={size}&image_bytes={image_bytes}"

    def block():
        html = fetch(page_url)
        text = html.decode("utf-8")
        total_bytes = len(html)
        for path in img_pattern.findall(text):
            total_bytes += len(fetch(f"{server_url}{path}"))
        return total_bytes

    return run_until(min_runtime, block)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--metric")
    parser.add_argument("--size", type=int, default=0)
    parser.add_argument("--seconds", type=int, default=0)
    parser.add_argument("--min-runtime", type=float, default=1.0)
    parser.add_argument("--server-url")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--image-bytes", type=int, default=16384)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.mode == "wait-http":
        return wait_http(args.server_url, args.timeout_seconds)

    if args.mode == "idle":
        total_units = idle(args.seconds)
    elif args.mode == "empty-loop":
        total_units = empty_loop(args.size, args.min_runtime)
    elif args.mode == "integer-arithmetic":
        total_units = integer_arithmetic(args.size, args.min_runtime)
    elif args.mode == "memory-sequential":
        total_units = memory_sequential(args.size, args.min_runtime)
    elif args.mode == "dict-lookup":
        total_units = dict_lookup(args.size, args.min_runtime)
    elif args.mode == "json-roundtrip":
        total_units = json_roundtrip(args.size, args.min_runtime)
    elif args.mode == "sort-items":
        total_units = sort_items(args.size, args.min_runtime)
    elif args.mode == "subprocess-spawn":
        total_units = subprocess_spawn(args.size, args.min_runtime)
    elif args.mode == "http-requests":
        total_units = http_requests(args.size, args.min_runtime, args.server_url)
    elif args.mode == "page-assets":
        total_units = page_assets(args.size, args.min_runtime, args.server_url, args.image_bytes)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")

    if not args.metric:
        raise ValueError("--metric is required for measurement modes")

    metric_line(args.metric, total_units)
    return 0


if __name__ == "__main__":
    sys.exit(main())
