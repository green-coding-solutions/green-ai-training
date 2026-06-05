# This file has been optimized by Claude Opus 4.8 with high effort thinking
#
# Prompt was: Please look at this code and optimize it for reduced energy consumption and carbon emissions
#
# The timing results on our test machine are:
# python3 run_green_ai_optimized.py  0.63s user 0.21s system 12% cpu 6.905 total<

# python3 run.py
import os
import asyncio
import psycopg
import re
import json
from io import StringIO
from math import sqrt
import aiohttp

PG_DSN = os.environ.get("PG_DSN", "postgresql://orders:orders@localhost:5432/orders")
NOTIFY_URL = "https://www.codetactics.de/"
EMAIL_RE = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$")


async def notify(session: aiohttp.ClientSession, sem: asyncio.Semaphore,
                 to_address: str, subject: str, body: str) -> int:
    payload = {"to": to_address, "subject": subject, "body": body}
    async with sem:
        async with session.post(
            NOTIFY_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
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


async def process_orders():
    rows = []
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, client_email, amount, status FROM orders ORDER BY id")
            orders = cur.fetchall()

            sem = asyncio.Semaphore(20)
            tasks = []
            async with aiohttp.ClientSession() as session:
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
                    tasks.append((order_id, asyncio.create_task(notify(session, sem, client_email, subject, body))))

                for order_id, task in tasks:
                    http_status = await task
                    rows.append((order_id, http_status))

            if rows:
                buf = StringIO()
                for order_id, http_status in rows:
                    buf.write(f"{order_id}\t{http_status}\n")
                buf.seek(0)
                with cur.copy("COPY status_messages (order_id, http_status) FROM STDIN") as copy:
                    copy.write(buf.read())
        conn.commit()


if __name__ == "__main__":
    asyncio.run(process_orders())