import asyncio
import json
import os
import pathlib
from zipfile import ZipFile

import aiohttp
from dotenv import load_dotenv

from common.api_client import APIHandler
from common.ollama_api_client import OllamaAPIClient

SYSTEM_PROMPT = """
<objective>
    Classify the text into one of the categories: people, hardware, neither.
</objective>

<rules>
    Response should be valid JSON with keys: reasoning, category.
    Category should be one of: people, hardware, neither.
    Use only one word as a category.
    Please classify notes containing information about captured people or traces of their presence by guards and fixed hardware faults (ignore those related to software)
    Ignore mentions of people that are not related to the guards.
</rules>

<examples>
    Example 1: 
    Text: "Wykryto jednostkę organiczną w pobliżu północnego skrzydła fabryki. Skan biometryczny."
    Response: {"reasoning": "<REASONING>", "category": "people"}
</examples>
"""

PROMPT = """
Here are the text::
{text}
"""

load_dotenv()
WHISPER_URL = os.getenv("WHISPER_URL")


class TextExtractor:
    def __init__(self, files: list, session: aiohttp.ClientSession) -> None:
        self.files = files
        self.session = session
        self.ollama_client = OllamaAPIClient(session=session)

    async def process(self):
        texts = {
            "people": [],
            "hardware": [],
        }
        for file in self.files:
            extraction = ""
            if file.suffix == ".txt":
                extraction = self._extract_text(file)
            elif file.suffix == ".mp3":
                extraction = await self._extract_audio(file)
            elif file.suffix == ".png":
                extraction = await self._extract_images(file)

            self.ollama_client.model = "qwen2.5:32b"
            response = await self.ollama_client.get_response(
                prompt=PROMPT.format(text=extraction),
                system_prompt=SYSTEM_PROMPT,
            )

            category = json.loads(response)[
                "category"
            ]  # print(f"Response {file.name}: {category}")
            if category.lower().strip() in texts:
                texts[category.lower().strip()].append(file.name)

        return texts

    def _extract_text(self, file):
        with open(file, "r") as f:
            return f.read()

    async def _extract_audio(self, file):
        form = aiohttp.FormData()
        with file.open("rb") as f:
            form.add_field("file", f, filename=file.name, content_type="audio/mp3")
            form.add_field("response_format", "text")
            async with self.session.post(WHISPER_URL, data=form) as response:
                transcript = await response.text()
                return transcript

    async def _extract_images(self, file):
        self.ollama_client.model = "llama3.2-vision:latest"
        return await self.ollama_client.get_response(
            prompt="Extract only text from the image in original language. Do not make comments or notes.",
            system_prompt="You have perfect vision and you extract original text from the image.",
            images=[file],
        )


class ClassificationHandler:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.directory = pathlib.Path(__file__).parent.resolve()
        self.zip_filename = "pliki_z_fabryki.zip"
        self.path = self.directory / self.zip_filename
        self.extraction_path = self.directory / "extracted"
        self.data_url = f"https://centrala.ag3nts.org/dane/{self.zip_filename}"

    async def process(self):
        await self._download_data()
        self._extract_data()
        files = self._get_files()

        text_extractor = TextExtractor(files=files, session=self.session)
        texts = await text_extractor.process()
        return texts

    async def _download_data(self):
        if pathlib.Path(self.path).exists():
            return

        async with self.session.get(self.data_url, ssl=False) as response:
            file = await response.read()
        with open(self.path, "wb") as f:
            f.write(file)

    def _extract_data(self):
        with ZipFile(self.path, "r") as zip_ref:
            zip_ref.extractall(self.extraction_path)

    def _get_files(self):
        extensions = {".txt", ".mp3", ".png"}
        files_with_extensions = [
            file for file in self.extraction_path.glob("*") if file.suffix in extensions
        ]
        return files_with_extensions


async def main():
    async with aiohttp.ClientSession() as session:
        classification_handler = ClassificationHandler(session=session)
        texts = await classification_handler.process()
        print("Texts: ", texts)

        api_handler = APIHandler(session=session)
        response = await api_handler.send_report(data=texts, task="kategorie")
        print("Flag: ", response)


if __name__ == "__main__":
    asyncio.run(main())
