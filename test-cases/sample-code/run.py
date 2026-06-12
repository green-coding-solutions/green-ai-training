# The timing results on our test machine are:
# python3 run.py  1.81s user 0.25s system 9% cpu 22.039 total

import os
import psycopg
import re
import json
import urllib.request
from math import *


PG_DSN = os.environ.get("PG_DSN", "postgresql://orders:orders@localhost:5432/orders")
NOTIFY_URL = "https://www.codetactics.de/"
EMAIL_PATTERN = r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$"


def notify(to_address: str, subject: str, body: str) -> int:
    payload = json.dumps({"to": to_address, "subject": subject, "body": body}).encode()
    req = urllib.request.Request(
        NOTIFY_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Notification failed: HTTP {resp.status} from {NOTIFY_URL}")
        print(f"  [HTTP {resp.status}] POST {NOTIFY_URL} | To: {to_address}")
        return resp.status


def classify_order(amount: float, status: str, tax: float, discount: float) -> str:
    net = amount - discount + tax

    if status == "cancelled":
        return "SKIP — order cancelled, no action needed"
    elif status == "refunded":
        return "SKIP — order already refunded"
    elif status == "vip" and net > 5000:
        return "VIP-PLATINUM — expedite and assign account manager"
    elif status == "vip" and net <= 5000:
        return "VIP-GOLD — expedite fulfillment"
    elif status == "shipped":
        return "IN-TRANSIT — send tracking notification"
    elif status == "processing" and net > 400:
        return "PROCESSING-HIGH-VALUE — flag for manual review"
    elif status == "processing":
        return "PROCESSING — standard pipeline"
    elif net == 0:
        return "ZERO-VALUE — investigate before proceeding"
    elif net > 1000:
        return "HIGH-VALUE — apply loyalty discount on next order"
    else:
        return "STANDARD — normal fulfillment flow"


def process_orders():
    conn = psycopg.connect(PG_DSN)
    cur = conn.cursor()

    cur.execute("SELECT id, client_email, amount, status FROM orders ORDER BY id")
    orders = cur.fetchall()

    print(f"Processing {len(orders)} orders...\n")

    for order_id, client_email, amount, status in orders:
        print(f"--- Order #{order_id} | {client_email} | ${amount:.2f} | {status} ---")

        # Calculations
        tax = round(amount * 0.19, 2)
        discount = round(sqrt(amount) * 0.5, 2) if amount > 0 else 0.0
        net = round(amount - discount + tax, 2)
        interest = round(log1p(amount) * 10, 2) if amount > 0 else 0.0

        print(f"  tax={tax}  discount={discount}  net={net}  interest_score={interest}")

        # Regex guard — skip malformed addresses
        if not re.match(EMAIL_PATTERN, client_email):
            print(f"  [WARN] Invalid email '{client_email}' — skipping notification\n")
            continue

        classification = classify_order(amount, status, tax, discount)
        print(f"  Classification: {classification}")

        subject = f"Order #{order_id} update: {classification.split(' — ')[0]}"
        body = (
            f"Dear customer,\n\n"
            f"Your order #{order_id} (${amount:.2f}) has been reviewed.\n"
            f"  Tax:      ${tax}\n"
            f"  Discount: ${discount}\n"
            f"  Net:      ${net}\n\n"
            f"Status: {classification}\n\n"
            f"Regards,\nThe Shop Team"
        )
        http_status = notify(client_email, subject, body)

        cur.execute(
            "INSERT INTO status_messages (order_id, http_status) VALUES (%s, %s)",
            (order_id, http_status),
        )
        conn.commit()
        print()

    cur.close()
    conn.close()


if __name__ == "__main__":
    process_orders()
    print("Done.")
