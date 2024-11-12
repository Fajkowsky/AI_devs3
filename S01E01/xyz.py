import asyncio
import re

import aiohttp

from common.ollama_api_client import OllamaAPIClient

PROMPT_TEMPLATE = "Answer the question with only the year.\nQuestion: {question}"


class FormHandler:
    FORM_URL = "https://xyz.ag3nts.org/"
    FORM_USERNAME = "tester"
    FORM_PASSWORD = "574e112a"

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def get_question(self) -> str:
        async with self.session.get(self.FORM_URL, ssl=False) as response:
            page_text = await response.text()
        match = re.search(
            r'<p id="human-question">(?:Question:<br />)?(.*?)</p',
            page_text,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1).strip() if match else ""

    async def submit_answer(self, answer: str) -> str:
        form_data = {
            "username": self.FORM_USERNAME,
            "password": self.FORM_PASSWORD,
            "answer": answer,
        }
        async with self.session.post(self.FORM_URL, data=form_data, ssl=False) as response:
            return await response.text()

    def get_flag(self, text: str) -> str:
        match = re.search(r"\{\{FLG:[^}]+\}\}", text)
        return match.group(0) if match else ""


async def main():
    async with aiohttp.ClientSession() as session:
        form_handler = FormHandler(session)
        api_client = OllamaAPIClient(session=session)

        question = await form_handler.get_question()
        print(f"Found question: {question}")

        prompt = PROMPT_TEMPLATE.format(question=question)
        answer = await api_client.get_response(prompt)
        print(f"Answer: {answer}")

        response = await form_handler.submit_answer(answer=answer)
        flag = form_handler.get_flag(response)
        print(f"Flag: {flag}")


if __name__ == "__main__":
    asyncio.run(main())
