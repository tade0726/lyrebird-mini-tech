from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.database import get_session
from api.utils.logging import get_logger
from api.utils.security import get_current_user
from api.schemas import (
    DictationsCreateResponse,
    UserEditsInput,
    UserPreferencesResponse,
)
from api.services.audio_service import AudioService, PreferencesService
from api.models import UserModel

logger = get_logger(__name__)

router = APIRouter(prefix="/dictations", tags=["dictations"])


@router.post(
    "/", response_model=DictationsCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_dictation(
    audio: UploadFile = File(..., description="Audio file to be processed"),
    session: AsyncSession = Depends(get_session),
    user: UserModel = Depends(get_current_user),
) -> DictationsCreateResponse:
    """Accept an audio file for dictation processing."""

    # Validate file type
    allowed_content_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg"]
    if audio.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join([t.split('/')[-1] for t in allowed_content_types])}",
        )

    # Validate file size (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await audio.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB",
        )

    try:
        audio_service = AudioService(session)
        return await audio_service.process_audio(content, user.id)
    except Exception as e:
        logger.error(f"Error processing dictation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the audio file",
        )


@router.post("/preference_extract", response_model=UserPreferencesResponse)
async def preference_extract(
    original_text: str,
    edited_text: str,
    session: AsyncSession = Depends(get_session),
    user: UserModel = Depends(get_current_user),
) -> UserPreferencesResponse:
    """Extract user preferences from text edits."""

    user_edits = UserEditsInput(
        user_id=user.id,
        original_text=original_text,
        edited_text=edited_text,
    )

    preferences_service = PreferencesService(session)
    return await preferences_service.extract_preferences(user_edits)


@router.get("/preferences", response_model=List[UserPreferencesResponse])
async def get_user_preferences(
    session: AsyncSession = Depends(get_session),
    user: UserModel = Depends(get_current_user),
) -> List[UserPreferencesResponse]:
    """Get all user preferences."""

    preferences_service = PreferencesService(session)
    return await preferences_service.get_user_preferences(user.id)
