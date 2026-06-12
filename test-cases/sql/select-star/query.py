import psycopg
import os

conn = psycopg.connect(
    host=os.environ.get("PG_HOST", "localhost"),
    dbname=os.environ.get("PG_DB", "mydb"),
    user=os.environ.get("PG_USER", "user"),
    password=os.environ.get("PG_PASSWORD", "password"),
)
cur = conn.cursor()

cur.execute("SELECT * FROM products ORDER BY id LIMIT 1000")
rows = cur.fetchall()

cur.close()
conn.close()
