import asyncio
import sys
import aiohttp

URL = "https://codetactics.de"

async def fetch(session):
    async with session.get(URL) as response:
        await response.read()
        if response.status != 200:
            print(f"Expected HTTP 200, got {response.status}", file=sys.stderr)
            sys.exit(1)

async def main():
    async with aiohttp.ClientSession() as session:
        for _ in range(10):
            await fetch(session)

asyncio.run(main())
