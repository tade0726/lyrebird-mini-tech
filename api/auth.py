from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.database import get_session
from api.utils.logging import get_logger
from api.utils.security import (
    get_current_user,
    create_access_token,
    verify_password,
    get_password_hash,
)
from api.config import settings
from api.utils.exceptions import UnauthorizedException
from api.models import UserModel
from api.schemas import LoginData, Token, UserCreate, UserResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate, session: AsyncSession = Depends(get_session)
) -> UserResponse:
    """Register a new user."""
    logger.debug(f"Registering user: {user_data.email}")

    # Check if user exists
    stmt = select(UserModel).where(UserModel.email == user_data.email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = UserModel(email=user_data.email, hashed_password=hashed_password)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Authenticate user and return token."""
    login_data = LoginData(email=form_data.username, password=form_data.password)
    logger.debug(f"Login attempt: {login_data.email}")

    # Get user
    stmt = select(UserModel).where(UserModel.email == login_data.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(login_data.password, str(user.hashed_password)):
        raise UnauthorizedException(detail="Incorrect email or password")

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRATION),
    )

    logger.info(f"User authenticated: {user.email}")
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserModel = Depends(get_current_user)) -> UserResponse:
    """Get current authenticated user."""
    return UserResponse.model_validate(user)
