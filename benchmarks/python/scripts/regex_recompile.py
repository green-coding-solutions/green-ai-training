import re
import time

N = 10_000

PATTERN = (
    r'(?P<ip>(?:\d{1,3}\.){3}\d{1,3}|(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})'
    r'\s+(?P<ident>\S+)\s+(?P<user>\S+)'
    r'\s+\[(?P<time>[^\]]+)\]'
    r'\s+"(?P<method>GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(?P<path>[^\s"]+)\s+HTTP/(?P<version>\d+\.\d+)"'
    r'\s+(?P<status>[1-5]\d{2})\s+(?P<size>\d+|-)'
    r'\s+"(?P<referer>[^"]*?)"\s+"(?P<agent>[^"]*?)"'
    r'(?:\s+(?P<extra>\S+))?'
)
TEST = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://example.com/" "Mozilla/5.0"'

for _ in range(N):
    re.purge()
    re.match(PATTERN, TEST)

print(f"{time.time_ns()} regex_matches={N}")
