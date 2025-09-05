import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()
URLS = [os.getenv("TEAMS_URL"), os.getenv("GAMES_URL")]
TOKEN = os.getenv("TEAMS_TOKEN")


async def generate_data():
    headers = {"Authorization": TOKEN} if TOKEN else {}
    results = {}
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in URLS:
            try:
                async with session.get(url, timeout=10) as resp:
                    resp.raise_for_status()
                    results[url] = await resp.json()
            except Exception as e:
                results[url] = {"error": str(e)}
    return results
