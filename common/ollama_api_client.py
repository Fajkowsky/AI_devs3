import base64
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

    async def get_response(
        self,
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        images: list = None,
    ) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": system_prompt,
        }
        if images:
            payload["images"] = [self._convert_image_to_base64(image) for image in images]
        async with self.session.post(self.url, json=payload, ssl=False) as response:
            result = await response.json()
            return result.get("response", "")

    def _convert_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
