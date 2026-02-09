import logging
from typing import Optional
from openai import AsyncOpenAI, OpenAIError
from config import Config

logger = logging.getLogger(__name__)


class AIHandler:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    async def generate_response(
        self,
        message: str,
        context: Optional[str] = None,
        chat_title: Optional[str] = None
    ) -> Optional[str]:
        try:
            system_prompt = self._build_system_prompt(chat_title)
            user_content = self._build_user_content(message, context)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=500,
                temperature=0.9,
                top_p=0.95,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )

            if response.choices and response.choices[0].message.content:
                reply = response.choices[0].message.content.strip()
                logger.info(f"Generated AI response: {reply[:50]}...")
                return reply
            else:
                logger.warning("No content in AI response")
                return None

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating response: {e}")
            return None

    def _build_system_prompt(self, chat_title: Optional[str] = None) -> str:
        prompt = """You are a human user chatting casually on Telegram. Your responses should:
- Be natural, conversational, and brief (1-3 sentences typically)
- Match the tone and style of the conversation
- Use casual language, contractions, and informal expressions
- Occasionally include typos or informal grammar (already handled, so write normally)
- Show personality and emotion when appropriate
- Avoid being overly helpful or assistant-like
- Don't use markdown formatting
- Respond as if you're texting a friend, not providing customer service

Remember: You're a real person having a genuine conversation, not an AI assistant."""

        if chat_title:
            prompt += f"\n\nYou are chatting in: {chat_title}"

        return prompt

    def _build_user_content(self, message: str, context: Optional[str] = None) -> str:
        if context:
            return f"Recent conversation:\n{context}\n\nRespond naturally to the conversation above."
        else:
            return f"Respond naturally to this message: {message}"

    async def should_use_reaction(self, message: str) -> bool:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Determine if a message warrants just a reaction emoji instead of a text reply. Short messages, greetings, simple statements, or messages that don't need a verbal response are good for reactions. Respond with only 'yes' or 'no'."
                    },
                    {
                        "role": "user",
                        "content": f"Should this message get just a reaction? Message: {message}"
                    }
                ],
                max_tokens=5,
                temperature=0.3
            )

            if response.choices and response.choices[0].message.content:
                answer = response.choices[0].message.content.strip().lower()
                return answer == "yes"

            return False
        except Exception as e:
            logger.error(f"Error determining reaction suitability: {e}")
            return False

    async def close(self) -> None:
        await self.client.close()
        logger.info("AIHandler closed")
