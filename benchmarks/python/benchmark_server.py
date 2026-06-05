from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import json


class BenchmarkHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/health":
            self.respond(200, b"ok", "text/plain; charset=utf-8")
            return

        if parsed.path == "/json":
            payload = json.dumps({"status": "ok", "value": 42, "items": [1, 2, 3]}).encode("utf-8")
            self.respond(200, payload, "application/json")
            return

        if parsed.path == "/page":
            image_count = int(query.get("images", ["1"])[0])
            image_bytes = int(query.get("image_bytes", ["16384"])[0])
            images = "\n".join(
                f'<img src="/image/{index}?bytes={image_bytes}" alt="bench-{index}">'
                for index in range(image_count)
            )
            html = (
                "<!doctype html><html><head><title>Bottom Up Bench</title></head>"
                f"<body><h1>Assets</h1>{images}</body></html>"
            ).encode("utf-8")
            self.respond(200, html, "text/html; charset=utf-8")
            return

        if parsed.path.startswith("/image/"):
            image_bytes = int(query.get("bytes", ["16384"])[0])
            payload = bytes((index % 251 for index in range(image_bytes)))
            self.respond(200, payload, "application/octet-stream")
            return

        self.respond(404, b"not found", "text/plain; charset=utf-8")

    def log_message(self, format, *args):
        return

    def respond(self, status_code, payload, content_type):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), BenchmarkHandler).serve_forever()
