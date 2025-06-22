from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.models import DictationsModel, UserEditsModel, UserPreferencesModel
from api.schemas import (
    DictationsCreate,
    DictationsCreateResponse,
    UserEditsInput,
    UserPreferencesCreate,
    UserPreferencesResponse,
)
from api.services.llm_service import LLMService
from api.utils.logging import get_logger

logger = get_logger(__name__)


class AudioService:
    """Service for handling audio transcription and formatting."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm_service = LLMService()

    async def process_audio(
        self, audio_data: bytes, user_id: int
    ) -> DictationsCreateResponse:
        """Process audio file: transcribe and format."""
        try:
            # Transcribe audio
            transcript = await self.llm_service.transcribe_audio(audio_data)

            # Get user preferences
            preferences = await self._get_user_preferences(user_id)

            # Format transcript
            formatted_text = await self.llm_service.format_transcript(
                transcript, preferences
            )

            # Save to database
            dictation_data = DictationsCreate(
                text=transcript, formatted_text=formatted_text, user_id=user_id
            )

            dictation = DictationsModel(**dictation_data.model_dump())
            self.session.add(dictation)
            await self.session.commit()
            await self.session.refresh(dictation)

            return DictationsCreateResponse.model_validate(dictation)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Audio processing failed: {str(e)}")
            raise

    async def _get_user_preferences(self, user_id: int) -> List[str]:
        """Get user preferences as list of strings."""
        stmt = select(UserPreferencesModel).where(
            UserPreferencesModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        preferences = result.scalars().all()
        return [pref.rules for pref in preferences if pref.rules]


class PreferencesService:
    """Service for handling user preferences."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm_service = LLMService()

    async def extract_preferences(
        self, user_edits_input: UserEditsInput
    ) -> UserPreferencesResponse:
        """Extract and save user preferences from edits."""
        try:
            # Save user edit
            user_edit = UserEditsModel(**user_edits_input.model_dump())
            self.session.add(user_edit)
            await self.session.flush()  # Get ID without committing

            # Get existing preferences
            existing_preferences = await self._get_user_preferences_list(
                user_edits_input.user_id
            )

            # Extract new preference
            new_preference = await self.llm_service.extract_user_preferences(
                user_edits_input.original_text,
                user_edits_input.edited_text,
                existing_preferences,
            )

            # Save preference if extracted
            preference_model = None
            if new_preference:
                preference_data = UserPreferencesCreate(
                    user_id=user_edits_input.user_id,
                    user_edits_id=user_edit.id,
                    rules=new_preference,
                )
                preference_model = UserPreferencesModel(**preference_data.model_dump())
                self.session.add(preference_model)
                await self.session.flush()

            await self.session.commit()

            return UserPreferencesResponse(
                id=preference_model.id if preference_model else None,
                user_id=user_edits_input.user_id,
                rules=new_preference,
                user_edits_id=user_edit.id,
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Preference extraction failed: {str(e)}")
            raise

    async def get_user_preferences(self, user_id: int) -> List[UserPreferencesResponse]:
        """Get all user preferences."""
        stmt = select(UserPreferencesModel).where(
            UserPreferencesModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        preferences = result.scalars().all()
        return [UserPreferencesResponse.model_validate(pref) for pref in preferences]

    async def _get_user_preferences_list(self, user_id: int) -> List[str]:
        """Get user preferences as list of strings."""
        stmt = select(UserPreferencesModel).where(
            UserPreferencesModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        preferences = result.scalars().all()
        return [pref.rules for pref in preferences if pref.rules]
