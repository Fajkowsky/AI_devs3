import asyncio
import os

import aiohttp
from dotenv import load_dotenv
from openai import OpenAI

from common.api_client import APIHandler
from common.ollama_api_client import OllamaAPIClient

SYSTEM_PROMPT = """
Based on the description of the vehicle provide input for image generation prompt.
Focus on the vehicle details.
Focus on the facts.
Give me only prompt for the image generation.
"""

PROMPT = """
Description of the vehicle: {description}
"""

load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")


class ImageHandler:
    def __init__(self):
        self.client = OpenAI(api_key=OPEN_AI_KEY)

    async def process(self, input: str):
        response = self.client.images.generate(
            model="dall-e-3", prompt=input, size="1024x1024"
        )
        return response.data[0].url


async def main():
    async with aiohttp.ClientSession() as session:
        api_handler = APIHandler(session)
        response = await api_handler.get_data("robotid.json")
        description = response.get("description")
        print(f"Description: {description}")

        ollama_client = OllamaAPIClient(session=session, model="gemma2:27b")
        response = await ollama_client.get_response(
            prompt=PROMPT.format(description=description),
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"Vehicle: {response}")

        image_handler = ImageHandler()
        image_url = await image_handler.process(input=response)
        print(f"Image: {image_url}")

        response = await api_handler.send_report(data=image_url, task="robotid")
        print("Flag: ", response)


if __name__ == "__main__":
    asyncio.run(main())
