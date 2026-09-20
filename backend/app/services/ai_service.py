from .json_service import JSONService
from .ai_prompt_service import AIPromptService
from .ai_schema_service import AISchemaService
from models import AIPromptType
from openai import (
    AsyncOpenAI,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
)
import os
import json
import asyncio
import random
from typing import Any

class AIService:
    def __init__(self):
        self.gpt_model = "gpt-4.1-nano"
        self.async_openai_client = AsyncOpenAI(api_key = os.getenv("OPENAI_API_KEY"))
        self.json_service = JSONService()
        self.ai_prompt_service = AIPromptService()
        self.ai_schema_service = AISchemaService()

    async def fetch_ai_data(
        self,
        prompt_type: AIPromptType,
        prompt_prams: dict,
        prompt_input: Any
    ) -> dict:

        max_retries = 5

        prompt = self.ai_prompt_service.get_prompt(prompt_type, prompt_prams)
        schema = self.ai_schema_service.get_schema(prompt_type)

        for attempt in range(max_retries):
            try:
                response = await self.retry_with_backoff(
                    lambda: self.async_openai_client.responses.create(
                                model="gpt-4.1-nano",
                                instructions=prompt,
                                input=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                            "type": "input_text",
                                            "text": json.dumps(prompt_input, ensure_ascii=False)
                                            }
                                        ]
                                    }
                                ],
                                text=schema,
                                reasoning={},
                                stream=False,
                                store=True,
                                include=["web_search_call.action.sources"]
                            )
                )

                result = json.loads(response.output_text)
                return result

            except (json.JSONDecodeError, ValueError) as e:

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Failed to get valid AI data for "
                        f"{prompt_type} after {max_retries} attempts. "
                        f"Last error: {e}"
                    ) from e

                delay = 1 * (2 ** attempt) + random.uniform(0, 0.5)

                print(
                    f"Invalid AI response. "
                    f"Retrying in {delay:.2f}s..."
                )

                await asyncio.sleep(delay)

    async def retry_with_backoff(
        self,
        operation,
        retries=5,
        base_delay=1
    ):
        for attempt in range(retries):
            try:
                return await operation()

            except (
                RateLimitError,
                APIConnectionError,
                APITimeoutError,
                InternalServerError,
            ) as e:

                if attempt == retries - 1:
                    raise

                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)

                print(
                    f"{type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                await asyncio.sleep(delay)