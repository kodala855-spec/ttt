import logging
import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from openai import APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)


class AIHandler:
    def __init__(self, api_key: str, system_prompt: str, timeout: int = 30):
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.system_prompt = system_prompt
        self.timeout = timeout
        logger.info(f"AIHandler initialized with timeout={timeout}s")
    
    async def get_response(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> Optional[str]:
        try:
            full_messages = [
                {"role": "system", "content": self.system_prompt}
            ] + messages
            
            logger.debug(f"Requesting AI response with {len(messages)} messages")
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=full_messages,
                    temperature=0.7,
                    max_tokens=500
                ),
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content
            logger.info(f"AI response received: {len(content)} characters")
            return content
            
        except asyncio.TimeoutError:
            logger.error(f"AI request timed out after {self.timeout}s")
            return None
        except APITimeoutError:
            logger.error("OpenAI API timeout")
            return None
        except RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            return None
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in AI handler: {e}")
            return None
    
    async def get_response_with_retry(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> Optional[str]:
        for attempt in range(max_retries):
            result = await self.get_response(messages, model)
            if result is not None:
                return result
            
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {retry_delay}s")
                await asyncio.sleep(retry_delay)
        
        logger.error(f"Failed to get AI response after {max_retries} attempts")
        return None
