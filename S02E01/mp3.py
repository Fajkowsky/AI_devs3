import asyncio
import os
import pathlib
from zipfile import ZipFile

import aiohttp
from dotenv import load_dotenv

from common.api_client import APIHandler
from common.ollama_api_client import OllamaAPIClient

SYSTEM_PROMPT = """
You need to deduce the location of the university where Andrzej Maj teaches and focus only of that.
Carefully analyze the given transcriptions to extract accurate information about where Andrzej Maj teaches. 
Disregard any irrelevant, conflicting, or deceptive statements that do not pertain to the location. 
"""

PROMPT_TRANSCRIPTION = """
Based on the following transcriptions from the interrogations, determine the departments of the university that employs Andrzej Maj.
Choose correct department address based on the transcriptions.

Here are the transcriptions from the interrogations:
{transcriptions}
"""

PROMPT_ADDRESS = """
Based on the summary of the transcriptions and your knowledge, determine the departments address of the university that employs Andrzej Maj.

Summary:
{summary}

Give onl the street name and number of the department.
"""

load_dotenv()
WHISPER_URL = os.getenv("WHISPER_URL")


class MP3Handler:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.zip_filename = "przesluchania.zip"
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(self.directory, self.zip_filename)
        self.extraction_path = os.path.join(self.directory, "extracted")
        self.data_url = f"https://centrala.ag3nts.org/dane/{self.zip_filename}"

    async def process(self):
        await self._download_data()
        self._extract_data()
        return await self._get_transcript()

    async def _download_data(self):
        if pathlib.Path(self.path).exists():
            return

        async with self.session.get(self.data_url, ssl=False) as response:
            file = await response.read()
        with open(self.path, "wb") as f:
            f.write(file)

    def _extract_data(self):
        if not os.path.exists(self.extraction_path):
            with ZipFile(self.path, "r") as zip_ref:
                zip_ref.extractall(self.extraction_path)

    async def _get_transcript(self):
        tasks = []
        for sound_file in pathlib.Path(self.extraction_path).glob("*.m4a"):
            text_file = sound_file.with_suffix(".txt")
            if not text_file.exists():
                tasks.append(self._process_sound(sound_file, text_file))
        await asyncio.gather(*tasks)

    async def _process_sound(self, sound_file: pathlib.Path, text_file: pathlib.Path):
        form = aiohttp.FormData()
        with sound_file.open("rb") as f:
            form.add_field(
                "file", f, filename=sound_file.name, content_type="audio/m4a"
            )
            form.add_field("response_format", "text")
            async with self.session.post(WHISPER_URL, data=form) as response:
                transcript = await response.text()
        with text_file.open("w") as f:
            f.write(transcript)

    def get_transcriptions(self):
        transcriptions = {}
        for text_file in pathlib.Path(self.extraction_path).glob("*.txt"):
            with text_file.open() as f:
                transcriptions[text_file.stem] = f.read()
        return "\n".join(f"{name}: {text}" for name, text in transcriptions.items())


async def main():
    async with aiohttp.ClientSession() as session:
        mp3_handler = MP3Handler(session)
        await mp3_handler.process()
        transcriptions = mp3_handler.get_transcriptions()

        ollama_client = OllamaAPIClient(session=session, model="nemotron")
        response = await ollama_client.get_response(
            prompt=PROMPT_TRANSCRIPTION.format(transcriptions=transcriptions),
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"Summary: {response}")
        response = await ollama_client.get_response(
            prompt=PROMPT_ADDRESS.format(summary=response),
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"Answer: {response}")

        api_handler = APIHandler(session=session)
        response = await api_handler.send_report(data=response, task="mp3")
        print("Flag: ", response)


if __name__ == "__main__":
    asyncio.run(main())
