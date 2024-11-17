import logging
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("CENTRALA_REPORT_API_URL")


class APIHandler:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str = API_KEY,
        api_url: str = API_URL,
    ) -> None:
        self.session = session
        self.api_key = api_key
        self.api_url = api_url

    async def get_data(self, postfix: str):
        url = f"https://centrala.ag3nts.org/data/{API_KEY}/{postfix}"
        async with self.session.get(url, ssl=False) as response:
            response.raise_for_status()
            return await response.json()

    async def send_report(self, data: str, task: str):
        payload = {"answer": data, "apikey": self.api_key, "task": task}
        return await self._post_request(self.api_url, payload)

    async def _post_request(self, url: str, payload: dict):
        try:
            async with self.session.post(url, json=payload, ssl=False) as response:
                response.raise_for_status()
                result = await response.json()
                return response.status, result.get("message", "")
        except aiohttp.ClientResponseError as e:
            logging.error(f"Client response error: {e}")
            return e.status, e.message
        except aiohttp.ClientError as e:
            logging.error(f"Client error: {e}")
            return None, str(e)

    async def close(self):
        await self.session.close()
