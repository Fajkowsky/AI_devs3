import asyncio
import os
import re

import aiohttp
from dotenv import load_dotenv

load_dotenv(".env")
OLLAMA_URL = os.getenv("OLLAMA_URL")
FORM_URL = "https://xyz.ag3nts.org/"
FORM_USERNAME = "tester"
FORM_PASSWORD = "574e112a"

SYSTEM_PROMPT = "You are assistant, answer only the question, no other information."
PROMPT_TEMPLATE = "Answer the question with only the year.\nQuestion: {question}"


class APIClient:
    def __init__(
        self, model="llama3.2", url=OLLAMA_URL, session: aiohttp.ClientSession = None
    ):
        self.model = model
        self.url = url
        self.session = session

    async def get_response(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": SYSTEM_PROMPT,
        }
        async with self.session.post(self.url, json=payload) as response:
            result = await response.json()
            return result.get("response", "")


class FormHandler:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def get_question(self, url: str) -> str:
        async with self.session.get(url) as response:
            page_text = await response.text()
        match = re.search(
            r'<p id="human-question">(?:Question:<br />)?(.*?)</p',
            page_text,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1).strip() if match else ""

    async def submit_answer(self, url: str, data: dict) -> str:
        async with self.session.post(url, data=data) as response:
            return await response.text()

    def get_flag(self, text: str) -> str:
        match = re.search(r"\{\{FLG:[^}]+\}\}", text)
        return match.group(0) if match else ""


async def main():
    async with aiohttp.ClientSession() as session:
        form_handler = FormHandler(session)
        api_client = APIClient(session=session)

        question = await form_handler.get_question(FORM_URL)
        print(f"Found question: {question}")

        prompt = PROMPT_TEMPLATE.format(question=question)
        answer = await api_client.get_response(prompt)
        print(f"Answer: {answer}")

        form_data = {
            "username": FORM_USERNAME,
            "password": FORM_PASSWORD,
            "answer": answer,
        }
        response = await form_handler.submit_answer(FORM_URL, form_data)
        flag = form_handler.get_flag(response)
        print(f"Flag: {flag}")


if __name__ == "__main__":
    asyncio.run(main())
