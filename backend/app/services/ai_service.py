from .json_service import JSONService
from .ai_prompt_service import AIPromptService
from models import Language, AIPromptType
from openai import AsyncOpenAI
import os
import json
import asyncio
import random

class AIService:
    def __init__(self):
        self.gpt_model = "gpt-4.1-nano"
        self.async_openai_client = AsyncOpenAI(api_key = os.getenv("OPENAI_API_KEY"))
        self.json_service = JSONService()
        self.ai_prompt_service = AIPromptService()

    async def fetch_ai_data(self, prompt_type: AIPromptType, params: dict) -> dict:
        max_retries = 5
        prompt = self.ai_prompt_service.get_prompt(prompt_type, params)
        json_validator_callback = self.json_service.get_validator_callback(prompt_type)

        for attempt in range(max_retries):
            response = await self.retry_with_backoff(
                self.async_openai_client.responses.create(
                    model=self.gpt_model,
                    input=prompt,
                    store=False
                )
            )

            raw_text = response.output[0].content[0].text.strip()
            try:
                parsed_json = json.loads(raw_text)
                json_validator_callback(parsed_json)
                return parsed_json
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__} - {e}. Retrying..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch AI data for prompt {prompt_type} after {max_retries} attempts. Last error: {e}") from e
                await asyncio.sleep(1)

    async def retry_with_backoff(self, coro, retries=5, base_delay=1):
        for attempt in range(retries):
            try:
                return await coro
            except Exception as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Operation failed after {retries} attempts. {str(e)}") from e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)