import json
import tempfile
from typing import List

from langsmith import Client as LangSmithClient
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI

from api.config import settings
from api.utils.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for handling LLM operations."""

    def __init__(self):
        self.openai_client = self._setup_openai_client()
        self.langsmith_client = LangSmithClient(api_key=settings.LANGSMITH_API_KEY)

    def _setup_openai_client(self) -> AsyncOpenAI:
        """Setup OpenAI client with LangSmith tracing."""
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return wrap_openai(client)

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using OpenAI Whisper."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mpga", delete=False) as f:
                f.write(audio_data)
                temp_filename = f.name

            with open(temp_filename, "rb") as audio_file:
                transcription = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )

            return transcription.text
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            raise

    async def format_transcript(self, transcript: str, preferences: List[str]) -> str:
        """Format transcript based on user preferences."""
        try:
            system_prompt = self.langsmith_client.pull_prompt(settings.FORMAT_PROMPT)

            system_message = {
                "role": "system",
                "content": system_prompt.format(foo="bar"),
            }

            user_message = {
                "role": "user",
                "content": f"""
                ### USER FORMATTING PREFERENCES
                {chr(10).join(preferences)}

                ### TRANSCRIPT TO PROCESS
                {transcript}
                """,
            }

            response = await self.openai_client.chat.completions.create(
                model=settings.DEFAULT_LLM_TEXT_MODEL,
                messages=[system_message, user_message],
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Transcript formatting failed: {str(e)}")
            raise

    async def extract_user_preferences(
        self, original_text: str, edited_text: str, existing_preferences: List[str]
    ) -> str | None:
        """Extract user preferences from text edits."""
        try:
            system_prompt = self.langsmith_client.pull_prompt(
                settings.EXTRACT_RULES_PROMPT
            )

            system_message = {
                "role": "system",
                "content": system_prompt.format(foo="bar"),
            }

            user_message = {
                "role": "user",
                "content": f"""
                ### ORIGINAL AI VERSION 
                {original_text}

                ### USER-EDITED VERSION 
                {edited_text}

                ### EXISTING USER PREFERENCES 
                {chr(10).join(existing_preferences)}
                """,
            }

            response = await self.openai_client.chat.completions.create(
                model=settings.DEFAULT_LLM_TEXT_MODEL,
                messages=[system_message, user_message],
                response_format={"type": "json_object"},
            )

            rules = json.loads(response.choices[0].message.content)
            logger.debug(f"Extracted rules: {rules}")

            return (
                rules.get("memory_to_write") if rules.get("memory_to_write") else None
            )

        except Exception as e:
            logger.error(f"Preference extraction failed: {str(e)}")
            return None
