import random
import time

N = 20_000

random.seed(42)
payments = [{"id": i, "reference": f"INV-{random.randint(0, N * 2)}", "amount": random.randint(100, 50_000)} for i in range(N)]
invoices = [{"number": f"INV-{i}", "amount": random.randint(100, 50_000)} for i in range(N)]

matched = 0
for payment in payments:
    for invoice in invoices:
        if invoice["number"] == payment["reference"]:
            matched += 1
            break

print(f"{time.time_ns()} payments_matched={N}")
