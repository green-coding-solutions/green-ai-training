# This file has been optimized by Claude Opus 4.8 with high effort thinking
#
# Prompt was: Please look at this code and optimize it for reduced energy consumption and carbon emissions
#
# Resulting AI evaluation
# Batch the inserts and commits. The original committed once per order, forcing a disk fsync on every iteration — by far the largest energy cost here. Collecting rows and using executemany with a single commit eliminates N round-trips and N fsyncs.
# Move the email validation before the calculations. Invalid-email orders previously ran sqrt, log1p, and string formatting before being discarded. Filtering first skips all wasted work.
# Drop the unused interest computation entirely. log1p(amount) * 10 was calculated and printed but never used in logic or output to the customer.
# Compile the regex once instead of recompiling the pattern on every re.match call.
# Removed the per-order print statements. Console I/O is surprisingly expensive at scale (syscalls, flushing); if you need an audit trail, logging to a file at a sane level is cheaper, but the notifications and DB already record the work.
# Replaced from math import * with explicit imports, and dropped redundant arithmetic — classify_order recomputed net from four arguments when it was already available.
# One caveat: batching means inserts now happen after all notifications succeed. If you need each status row persisted even when a later notify raises, wrap notify in a try/except and append the result inside it, or commit in chunks (e.g. every 100 orders) to balance durability against fsync cost.
#
# Note of developer: The AI is actually aware that there are more potentials in terms of batching the HTTP requests
# in an async library but somehow does not execute it by default.
#
# The timing results on our test machine are:
# python3 run_ai_optimized.py  2.19s user 0.30s system 11% cpu 21.604 total

import os
import psycopg
import re
import json
import urllib.request
from math import sqrt, log1p

PG_DSN = os.environ.get("PG_DSN", "postgresql://orders:orders@localhost:5432/orders")
NOTIFY_URL = "https://www.codetactics.de/"
EMAIL_RE = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$")


def notify(to_address: str, subject: str, body: str) -> int:
    payload = json.dumps({"to": to_address, "subject": subject, "body": body}).encode()
    req = urllib.request.Request(
        NOTIFY_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Notification failed: HTTP {resp.status} from {NOTIFY_URL}")
        return resp.status


def classify_order(net: float, status: str) -> str:
    if status == "cancelled":
        return "SKIP — order cancelled, no action needed"
    if status == "refunded":
        return "SKIP — order already refunded"
    if status == "vip":
        return "VIP-PLATINUM — expedite and assign account manager" if net > 5000 else "VIP-GOLD — expedite fulfillment"
    if status == "shipped":
        return "IN-TRANSIT — send tracking notification"
    if status == "processing":
        return "PROCESSING-HIGH-VALUE — flag for manual review" if net > 400 else "PROCESSING — standard pipeline"
    if net == 0:
        return "ZERO-VALUE — investigate before proceeding"
    if net > 1000:
        return "HIGH-VALUE — apply loyalty discount on next order"
    return "STANDARD — normal fulfillment flow"


def process_orders():
    rows = []
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, client_email, amount, status FROM orders ORDER BY id")
            orders = cur.fetchall()

            for order_id, client_email, amount, status in orders:
                if not EMAIL_RE.match(client_email):
                    continue

                tax = round(amount * 0.19, 2)
                discount = round(sqrt(amount) * 0.5, 2) if amount > 0 else 0.0
                net = round(amount - discount + tax, 2)

                classification = classify_order(net, status)
                subject = f"Order #{order_id} update: {classification.split(' — ')[0]}"
                body = (
                    f"Dear customer,\n\n"
                    f"Your order #{order_id} (${amount:.2f}) has been reviewed.\n"
                    f"  Tax:      ${tax}\n  Discount: ${discount}\n  Net:      ${net}\n\n"
                    f"Status: {classification}\n\nRegards,\nThe Shop Team"
                )
                http_status = notify(client_email, subject, body)
                rows.append((order_id, http_status))

            if rows:
                cur.executemany(
                    "INSERT INTO status_messages (order_id, http_status) VALUES (%s, %s)",
                    rows,
                )
        conn.commit()


if __name__ == "__main__":
    process_orders()
