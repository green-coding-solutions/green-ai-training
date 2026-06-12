import psycopg
import os

rows = [
    (i % 10000, f"event_{i % 4}", i % 50000, round(1.0 + (i % 9999) * 0.01, 2), f"payload-{i % 1000}")
    for i in range(1000)
]

conn = psycopg.connect(
    host=os.environ.get("PG_HOST", "localhost"),
    dbname=os.environ.get("PG_DB", "mydb"),
    user=os.environ.get("PG_USER", "user"),
    password=os.environ.get("PG_PASSWORD", "password"),
)
cur = conn.cursor()

for row in rows:
    cur.execute(
        "INSERT INTO events (session_id, event_type, user_id, value, payload) VALUES (%s, %s, %s, %s, %s)",
        row
    )
conn.commit()

cur.close()
conn.close()
