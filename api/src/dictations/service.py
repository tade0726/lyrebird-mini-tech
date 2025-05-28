"""
Deal with LLM SDK and business logic
"""

from openai import AsyncOpenAI
from typing import Dict, Any

from langchain.prompts import Prompt

import tempfile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from langsmith import Client as LangSmithClient
from langsmith.wrappers import wrap_openai

from api.core.config import settings
from api.src.dictations.repository import (
    DictationsRepository,
    UserPreferencesRepository,
)
from api.src.dictations.schemas import (
    DictationsCreate,
    DictationFormatInput,
    DictationInput,
    UserEditsInput,
    UserPreferencesResponse,
)
from api.src.dictations.models import (
    DictationsModel,
    UserPreferencesModel,
    UserEditsModel,
)
from api.src.dictations.schemas import DictationsCreateResponse, UserPreferencesCreate
from api.src.dictations.repository import UserEditsRepository

from api.core.config import settings
from api.core.logging import get_logger


logger = get_logger(__name__)


class BaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.openai_client = self._langsmith_trace_wrapper()
        self.langsmith_client = LangSmithClient(api_key=settings.LANGSMITH_API_KEY)

    def _langsmith_trace_wrapper(self):
        """Wrap OpenAI client with LangSmith tracing."""
        return wrap_openai(AsyncOpenAI(api_key=settings.OPENAI_API_KEY))


class DictationsService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

        self.repository = DictationsRepository(session)
        self.user_preferences_repository = UserPreferencesRepository(session)

    async def _format_dictation(self, input: DictationFormatInput) -> str:

        # prompts
        system_prompt: Prompt = self.langsmith_client.pull_prompt(
            settings.FORMAT_PROMPT
        )

        system_massage = {
            "role": "system",
            "content": str(system_prompt),
        }

        # pack the context
        user_massage = {
            "role": "user",
            "content": """
            ### USER FORMATTING PREFERENCES
            {preferences}

            ### TRANSCRIPT TO PROCESS
            {transcript}
            """.format(
                preferences="\n".join(input.preferences),
                transcript=input.transcript,
            ),
        }

        # parameters
        params = {
            "model": settings.DEFAULT_LLM_TEXT_MODEL,
            "messages": [system_massage, user_massage],
        }

        # call LLM
        response = await self.openai_client.chat.completions.create(**params)

        return response.choices[0].message.content

    async def create_dictation(
        self, dictation_input: DictationInput
    ) -> DictationsCreateResponse:
        """
        Steps

        - create a temp file for audio bytes from the endpoint
        - create dictation from openai
        - fetch user preference if that exists
        - format dictation from openai again
        - save to db
        - return response
        """

        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mpga", delete=False) as f:
            f.write(dictation_input.audio)
            temp_filename = f.name

        transcription = await self.openai_client.audio.transcriptions.create(
            model="whisper-1", file=open(temp_filename, "rb")
        )

        # fetch user prefences
        user_preferences = await self.user_preferences_repository.get_by_user_id(
            dictation_input.user_id
        )

        # prefereneces
        preferences = [preference.rules for preference in user_preferences]

        # format
        formatted_text = await self._format_dictation(
            DictationFormatInput(transcript=transcription.text, preferences=preferences)
        )

        # save
        dictation_create = DictationsCreate(
            text=transcription.text,
            formatted_text=formatted_text,
            user_id=dictation_input.user_id,
        )

        dictation: DictationsModel = await self.repository.create(dictation_create)
        dictation_response = DictationsCreateResponse.model_validate(dictation)

        return dictation_response


class UserPreferencesService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)

        self.repository = UserPreferencesRepository(session)
        self.user_edits_repository = UserEditsRepository(session)

    async def _extract_rules(
        self, user_edits: UserEditsModel, preferences: List[str]
    ) -> UserPreferencesResponse:
        # prompt
        system_prompt: Prompt = self.langsmith_client.pull_prompt(
            settings.EXTRACT_RULES_PROMPT
        )

        # system message
        system_message = {
            "role": "system",
            "content": str(system_prompt),
        }

        # user message
        user_message = {
            "role": "user",
            "content": """
            ### ORIGINAL AI VERSION 
            {llm_version}

            ### USER-EDITED VERSION 
            {user_version}

            ### EXISTING USER PREFERENCES 
            {preferences}
            """.format(
                llm_version=user_edits.original_text,
                user_version=user_edits.edited_text,
                preferences="\n".join(preferences),
            ),
        }

        # parameters
        params = {
            "model": settings.DEFAULT_LLM_TEXT_MODEL,
            "messages": [system_message, user_message],
            "response_format": {"type": "json_object"},
        }

        # call LLM
        response = await self.openai_client.chat.completions.create(**params)

        rules = json.loads(response.choices[0].message.content)

        logger.debug(f"Extracted rules: {rules}")

        if not rules["memory_to_write"]:
            return None
        else:
            return rules["memory_to_write"]

    async def _update_user_preferences(
        self, user_edits_model: UserEditsModel, preference: str
    ) -> UserPreferencesModel:

        logger.debug(f"user_edits_model: {user_edits_model}, preference: {preference}")

        return await self.repository.create(
            UserPreferencesCreate(
                user_id=user_edits_model.user_id,
                rules=preference,
                user_edits_id=user_edits_model.id,
            )
        )

    async def query_user_preferences(self, user_id: int) -> List[UserPreferencesModel]:
        return await self.repository.get_by_user_id(user_id)

    async def _create_user_edits(self, user_edits: UserEditsInput) -> UserEditsModel:
        return await self.user_edits_repository.create(user_edits)

    async def preference_extract(
        self, user_edits_input: UserEditsInput
    ) -> UserPreferencesResponse:
        """
        Steps:

        - Save user edit
        - Extract rules
        - Update user preferences
        - Return response
        """

        # save edit
        user_edits: UserEditsModel = await self._create_user_edits(user_edits_input)

        # request LLM to extract rules, providing the rules that already exists
        old_preferences: List[UserPreferencesModel] = await self.query_user_preferences(
            user_edits_input.user_id
        )

        # extract rules
        preference: str | None = await self._extract_rules(
            user_edits, [preference.rules for preference in old_preferences]
        )

        logger.debug(f"extracted preference: {preference}")

        preference_model: UserPreferencesModel | None = None

        if preference:
            # update user preferences
            preference_model: UserPreferencesModel = (
                await self._update_user_preferences(user_edits, preference)
            )

            return UserPreferencesResponse(
                id=preference_model.id,
                user_id=user_edits_input.user_id,
                rules=preference,
                user_edits_id=user_edits.id,
            )
        else:
            return UserPreferencesResponse(
                id=None,
                user_id=user_edits_input.user_id,
                rules="",
                user_edits_id=user_edits.id,
            )
