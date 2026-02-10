import asyncio
import logging
from typing import Dict, List, Optional

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError

logger = logging.getLogger(__name__)


class AIHandler:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        timeout: int = 30,
        temperature: float = 0.7,
        max_tokens: int = 350,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def get_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
        payload = [{"role": "system", "content": self.system_prompt}] + messages

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=payload,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                ),
                timeout=self.timeout,
            )
            content = response.choices[0].message.content if response.choices else None
            if not content:
                return None
            return content.strip()
        except asyncio.TimeoutError:
            logger.error("AI request timed out after %s seconds", self.timeout)
        except APITimeoutError:
            logger.error("OpenAI API timeout")
        except RateLimitError:
            logger.error("OpenAI rate limit exceeded")
        except APIConnectionError as exc:
            logger.error("OpenAI connection error: %s", exc)
        except APIError as exc:
            logger.error("OpenAI API error: %s", exc)
        except Exception as exc:
            logger.error("Unexpected AI error: %s", exc)
        return None
