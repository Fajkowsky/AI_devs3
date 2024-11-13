import asyncio
import pathlib

import aiohttp
from PIL import Image

from common.ollama_api_client import OllamaAPIClient

SYSTEM_PROMPT = """
You have perfect vision and pay great attention to detail.
You are looking at a map of a city, give me all street names.
Street is near black line.
Those are polish street names.
If something is not clear for street name then omit it.
Do not include any other information.
"""

PROMPT = """
Give me street names from map and only that.
"""

SYSTEM_PROMPT_CITY = """
Based on the street names and map locations from multiple maps.
Deduce the name of the city, street names are near each other.
One of the map is wrong.
Street names may contain typos.
Those are polish street names.

In the tag <REASONING> you can write your reasoning.
In the tag <CITY> you can write the name of the city.
"""

PROMPT_CITY = """
You are looking at a map of a city. You see the following streets:
{streets}
What is the name of the city?
"""


class MapHandler:
    def __init__(self):
        self.elements = {
            "map1.jpg": (330, 130, 830, 710),
            "map2.jpg": (930, 130, 1330, 710),
            "map3.jpg": (260, 760, 1350, 1250),
            "map4.jpg": (350, 1270, 1290, 1790),
        }
        self.directory = pathlib.Path(__file__).parent.resolve()
        self.map_path = self.directory / "map.jpeg"
        self.extracted_directory = self.directory / "extracted_maps"

    async def process(self):
        return self._extract_maps()

    def _extract_maps(self):
        self._ensure_directory()
        paths = []
        image = Image.open(self.map_path)
        for filename, coords in self.elements.items():
            path = self.extracted_directory / filename
            paths.append(path)
            if not path.exists():
                cropped_image = image.crop(coords)
                cropped_image.save(path)
        return paths

    def _ensure_directory(self):
        self.extracted_directory.mkdir(parents=True, exist_ok=True)


async def main():
    async with aiohttp.ClientSession() as session:
        mp3_handler = MapHandler()
        images = await mp3_handler.process()

        streets = {}
        ollama_client = OllamaAPIClient(session=session, model="llama3.2-vision")
        for number, image in enumerate(images):
            response = await ollama_client.get_response(
                prompt=PROMPT,
                system_prompt=SYSTEM_PROMPT,
                images=[image],
            )
            streets[f"map_{number + 1}"] = response

        ollama_client = OllamaAPIClient(session=session, model="llama3.1")
        response = await ollama_client.get_response(
            prompt=PROMPT_CITY.format(streets=streets),
            system_prompt=SYSTEM_PROMPT_CITY,
        )
        print("City name:", response)


if __name__ == "__main__":
    asyncio.run(main())
