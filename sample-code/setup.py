import os
import psycopg
import re
import json
import urllib.request
from math import *


PG_DSN = os.environ.get("PG_DSN", "postgresql://orders:orders@localhost:5432/orders")

FIRST_NAMES = [
    "alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi",
    "ivan", "judy", "karl", "linda", "mike", "nina", "oscar", "peggy",
    "quinn", "rachel", "steve", "tina", "ulrich", "vera", "walt", "xena",
    "yara", "zoe", "adam", "bella", "chris", "diana", "ethan", "fiona",
    "george", "hana", "igor", "julia", "kevin", "laura", "mario", "nora",
    "oliver", "paula", "roman", "sara", "tom", "uma", "victor", "wendy",
    "xavier", "yasmin",
]
DOMAINS = [
    "example.com", "corp.io", "mail.net", "inbox.org", "webmail.com",
    "fastmail.com", "proton.me", "outlook.com", "gmail.com", "yahoo.com",
]
STATUSES = ["pending", "pending", "pending", "processing", "shipped", "vip", "cancelled", "refunded"]
AMOUNTS = [
    0.00, 12.99, 22.10, 45.00, 85.00, 99.95, 150.25, 199.99, 300.00,
    450.75, 500.00, 750.00, 999.00, 1200.50, 1500.00, 2000.00, 3000.00,
    4500.00, 5000.00, 6000.00, 7300.00, 8000.00, 9999.99,
]

def init_db():
    conn = psycopg.connect(PG_DSN)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            client_email TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS status_messages (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            http_status INTEGER NOT NULL,
            sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute("DELETE FROM status_messages")
    cur.execute("DELETE FROM orders")
    orders = []
    # Seed a deliberately malformed address every ~50 rows to exercise the regex guard
    bad_email_ids = {3, 57, 112, 178, 234, 301, 389, 445, 498}
    for i in range(1, 100):
        if i in bad_email_ids:
            email = f"bad-address-{i}"
        else:
            name = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
            domain = DOMAINS[(i - 1) % len(DOMAINS)]
            email = f"{name}{i}@{domain}"
        amount = AMOUNTS[(i - 1) % len(AMOUNTS)]
        status = STATUSES[(i - 1) % len(STATUSES)]
        orders.append((i, email, amount, status))

    cur.executemany("INSERT INTO orders VALUES (%s, %s, %s, %s)", orders)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Done.")
