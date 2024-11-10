import asyncio
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv(".env")

DATA_URL = "https://poligon.aidevs.pl/dane.txt"
VERIFY_URL = os.getenv("POLIGON_VERIFY_API_URL")
API_KEY = os.getenv("API_KEY")


class APIClient:
    def __init__(self, url: str, api_key: str, session: aiohttp.ClientSession):
        self.url = url
        self.api_key = api_key
        self.session = session

    async def post_data(self, data: list) -> str:
        json_payload = {
            "task": "POLIGON",
            "apikey": self.api_key,
            "answer": data,
        }
        async with self.session.post(self.url, json=json_payload) as response:
            return await response.text()


async def start():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(DATA_URL) as resp:
                data = (await resp.text()).split()
            response_text = await APIClient(VERIFY_URL, API_KEY, session).post_data(data)
            print(response_text)
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(start())
