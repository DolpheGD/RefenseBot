"""
Standalone sanity check for TOPGG_TOKEN against top.gg's v1 API.

Run this after updating .env, before restarting the whole bot, to
confirm the token actually authenticates:

    .venv\\Scripts\\python check_topgg.py      (Windows)
    .venv/bin/python check_topgg.py            (macOS/Linux)

It does NOT touch the bot's database or Discord at all - it just hits
GET /projects/@me/votes with your token and prints what top.gg says.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

import aiohttp
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOPGG_TOKEN")


async def main():
    if not TOKEN:
        print("TOPGG_TOKEN is not set in .env - nothing to check.")
        return

    start_date = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://top.gg/api/v1/projects/@me/votes"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    params = {"startDate": start_date}

    print(f"GET {url}?startDate={start_date}")
    print("(showing only the response status/shape - not your token)\n")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            text = await resp.text()
            print(f"Status: {resp.status}")

            if resp.status == 200:
                import json
                data = json.loads(text)
                votes = data.get("data", [])
                print(f"Success. {len(votes)} vote record(s) in the last 48h.")
                if votes:
                    print("Most recent entry (raw):")
                    print(votes[0])
                print("\nTOPGG_TOKEN is valid for the v1 API.")
            elif resp.status == 401:
                print(
                    "401 Unauthorized - this token is not valid for the v1 API.\n"
                    "It's likely a legacy/v0 token (e.g. from the old webhook setup).\n"
                    "Generate a new one from your project's \"Integrations & API\"\n"
                    "settings on top.gg and put it in TOPGG_TOKEN in .env."
                )
            else:
                print(f"Unexpected response body:\n{text}")


if __name__ == "__main__":
    asyncio.run(main())
