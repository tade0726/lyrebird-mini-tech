from fastapi import APIRouter, Depends, File, Form, UploadFile, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_session
from api.core.logging import get_logger
from api.core.security import get_current_user
from api.src.dictations.schemas import (
    DictationsCreateResponse,
    DictationInput,
    UserEditsInput,
    UserPreferencesResponse,
)
from api.src.dictations.service import DictationsService, UserPreferencesService
from api.src.users.models import UserModel


# Set up logger for this module
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
    """
    Accept an audio file for dictation processing.

    The current user is injected from the Bearer token.

    Supported audio formats: .mp3, .wav, .m4a, .ogg
    Maximum file size: 10MB
    """
    # Validate file type
    allowed_content_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg"]
    if audio.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {', '.join([t.split('/')[-1] for t in allowed_content_types])}",
        )

    # Validate file size (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await audio.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is 10MB",
        )

    # Reset file cursor after reading
    await audio.seek(0)

    try:
        dictation_input = DictationInput(
            audio=content,
            user_id=user.id,
        )
        return await DictationsService(session).create_dictation(dictation_input)
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing dictation: {str(e)}")
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

    user_edits = UserEditsInput(
        user_id=user.id,
        original_text=original_text,
        edited_text=edited_text,
    )

    return await UserPreferencesService(session).preference_extract(user_edits)


@router.get("/preferences", response_model=list[UserPreferencesResponse])
async def get_user_preferences(
    session: AsyncSession = Depends(get_session),
    user: UserModel = Depends(get_current_user),
) -> list[UserPreferencesResponse]:
    return await UserPreferencesService(session).query_user_preferences(user.id)
