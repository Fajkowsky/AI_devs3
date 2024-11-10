import os

import aiohttp
from dotenv import load_dotenv

load_dotenv(".env")
OLLAMA_URL = os.getenv("OLLAMA_URL")

DEFAULT_SYSTEM_PROMPT = "You are assistant, answer question."


class OllamaAPIClient:
    def __init__(
        self, model="llama3.2", url=OLLAMA_URL, session: aiohttp.ClientSession = None
    ):
        self.model = model
        self.url = url
        self.session = session

    async def get_response(self, prompt: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": system_prompt,
        }
        async with self.session.post(self.url, json=payload) as response:
            result = await response.json()
            return result.get("response", "")
