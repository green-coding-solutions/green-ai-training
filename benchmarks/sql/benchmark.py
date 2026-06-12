#!/usr/bin/env python3
"""Benchmark: PostgreSQL SELECT and bulk INSERT methods.

SELECT modes: run a query for --repetitions iterations and emit queries_executed=<N>.
INSERT modes: insert a batch of --size rows for --repetitions iterations and emit rows_inserted=<N>.

The caller (usage_scenario YAML) picks the --mode and --size so that GMT
measures energy across identical workloads and normalises per unit of work done.
"""

import argparse
import csv
import io
import os
import sys
import time

import psycopg


def metric_line(metric_name, value):
    print(f"{time.time_ns()} {metric_name}={int(value)}", flush=True)


def get_conn(retries=30, delay=2):
    host     = os.environ.get("PG_HOST",     "postgres")
    port     = int(os.environ.get("PG_PORT", "5432"))
    dbname   = os.environ.get("PG_DB",       "benchmark_db")
    user     = os.environ.get("PG_USER",     "bench")
    password = os.environ.get("PG_PASSWORD", "bench123")
    for attempt in range(retries):
        try:
            return psycopg.connect(
                host=host, port=port, dbname=dbname,
                user=user, password=password,
            )
        except psycopg.OperationalError:
            if attempt < retries - 1:
                time.sleep(delay)
    raise RuntimeError(f"Could not connect to PostgreSQL at {host}:{port} after {retries} attempts")


# ── SELECT queries ────────────────────────────────────────────────────────────

SELECT_QUERIES = {
    # Single-table product listing
    "select-star-products": (
        "SELECT * "
        "FROM products "
        "ORDER BY id "
        "LIMIT %(size)s"
    ),
    "select-named-products": (
        "SELECT id, sku, name, price, category, subcategory, brand, "
        "       stock_quantity, is_active, average_rating "
        "FROM products "
        "ORDER BY id "
        "LIMIT %(size)s"
    ),
    # JOIN: orders with their line items
    "select-star-join": (
        "SELECT * "
        "FROM orders o "
        "JOIN order_items oi ON o.id = oi.order_id "
        "ORDER BY o.id, oi.id "
        "LIMIT %(size)s"
    ),
    "select-named-join": (
        "SELECT o.id          AS order_id, "
        "       o.customer_id, "
        "       o.order_date, "
        "       o.status, "
        "       o.total_amount, "
        "       oi.id         AS item_id, "
        "       oi.product_id, "
        "       oi.quantity, "
        "       oi.unit_price, "
        "       oi.subtotal "
        "FROM orders o "
        "JOIN order_items oi ON o.id = oi.order_id "
        "ORDER BY o.id, oi.id "
        "LIMIT %(size)s"
    ),
    # Column-count progression on products (1 → 2 → 4 → 8 → MAX=SELECT *)
    # Columns are selected in table-definition order so each tier adds the
    # next columns exactly as they appear on disk.
    "select-1col-products": (
        "SELECT id "
        "FROM products "
        "ORDER BY id "
        "LIMIT %(size)s"
    ),
    "select-2col-products": (
        "SELECT id, sku "
        "FROM products "
        "ORDER BY id "
        "LIMIT %(size)s"
    ),
    "select-4col-products": (
        "SELECT id, sku, name, price "
        "FROM products "
        "ORDER BY id "
        "LIMIT %(size)s"
    ),
    "select-8col-products": (
        "SELECT id, sku, name, price, "
        "       compare_at_price, cost_price, category, subcategory "
        "FROM products "
        "ORDER BY id "
        "LIMIT %(size)s"
    ),
}

# ── INSERT constants ──────────────────────────────────────────────────────────

INSERT_QUERY = (
    "INSERT INTO bench_inserts (session_id, event_type, user_id, value, payload) "
    "VALUES (%s, %s, %s, %s, %s)"
)

COPY_SQL = (
    "COPY bench_inserts (session_id, event_type, user_id, value, payload) "
    "FROM STDIN (FORMAT CSV)"
)

INSERT_MODES = {"insert-loop", "insert-executemany", "insert-copy"}
ALL_MODES = set(SELECT_QUERIES) | INSERT_MODES


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_rows(size):
    event_types = ("click", "view", "purchase", "signup")
    return [
        (i % 10000, event_types[i % 4], i % 50000,
         round(1.0 + (i % 9999) * 0.01, 2), f"payload-{i % 1000}")
        for i in range(size)
    ]


def _make_csv_bytes(rows):
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue().encode()


def _do_insert(mode, cur, conn, rows, csv_bytes):
    if mode == "insert-loop":
        for row in rows:
            cur.execute(INSERT_QUERY, row)
    elif mode == "insert-executemany":
        cur.executemany(INSERT_QUERY, rows)
    else:  # insert-copy
        with cur.copy(COPY_SQL) as copy:
            copy.write(csv_bytes)
    conn.commit()


# ── Benchmark runners ─────────────────────────────────────────────────────────

def run_select_benchmark(mode, size, repetitions):
    query = SELECT_QUERIES[mode]
    conn = get_conn()
    cur = conn.cursor()

    # Warmup: prime PostgreSQL's shared buffer cache so the benchmark measures
    # serialisation + wire-protocol overhead, not cold I/O.
    for _ in range(3):
        cur.execute(query, {"size": size})
        cur.fetchall()

    for _ in range(repetitions):
        cur.execute(query, {"size": size})
        cur.fetchall()

    metric_line("queries_executed", repetitions)
    cur.close()
    conn.close()


def run_insert_benchmark(mode, size, repetitions):
    rows = _make_rows(size)
    csv_bytes = _make_csv_bytes(rows) if mode == "insert-copy" else None

    conn = get_conn()
    cur = conn.cursor()

    # Warmup
    cur.execute("TRUNCATE bench_inserts")
    conn.commit()
    for _ in range(3):
        _do_insert(mode, cur, conn, rows, csv_bytes)

    # Timed runs (fresh table)
    cur.execute("TRUNCATE bench_inserts")
    conn.commit()
    for _ in range(repetitions):
        _do_insert(mode, cur, conn, rows, csv_bytes)

    metric_line("rows_inserted", repetitions * size)
    cur.close()
    conn.close()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PostgreSQL SELECT and bulk INSERT benchmark"
    )
    parser.add_argument(
        "--mode", required=True, choices=sorted(ALL_MODES),
        help="Query/insert mode to run"
    )
    parser.add_argument(
        "--size", type=int, default=1000,
        help="Row limit for SELECT, or batch size for INSERT"
    )
    parser.add_argument(
        "--repetitions", type=int, default=1000,
        help="Number of iterations to run"
    )
    args = parser.parse_args()

    if args.mode in INSERT_MODES:
        run_insert_benchmark(args.mode, args.size, args.repetitions)
    else:
        run_select_benchmark(args.mode, args.size, args.repetitions)


if __name__ == "__main__":
    main()
