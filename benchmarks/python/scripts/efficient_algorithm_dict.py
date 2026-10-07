import random
import time

N = 20_000

random.seed(42)
payments = [{"id": i, "reference": f"INV-{random.randint(0, N * 2)}", "amount": random.randint(100, 50_000)} for i in range(N)]
invoices = [{"number": f"INV-{i}", "amount": random.randint(100, 50_000)} for i in range(N)]

invoice_numbers = {invoice["number"] for invoice in invoices}

matched = 0
for payment in payments:
    if payment["reference"] in invoice_numbers:
        matched += 1

print(f"{time.time_ns()} payments_matched={N}")
