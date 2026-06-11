import time
import asyncio
import sys
import httpx

URL = "https://www.codetactics.de/"

async def fetch(client):
    response = await client.get(URL)
    if response.status_code != 200:
        print(f"Expected HTTP 200, got {response.status_code}", file=sys.stderr)
        sys.exit(1)

async def main():
    async with httpx.AsyncClient() as client:
        for _ in range(10):
            await fetch(client)
        print(f"{time.time_ns()} http_requests=10")

asyncio.run(main())
