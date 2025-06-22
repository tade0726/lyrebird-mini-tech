from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """User creation schema."""

    password: str


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)
    id: int


class Token(BaseModel):
    """Token schema."""

    access_token: str
    token_type: str = "bearer"


class LoginData(BaseModel):
    """Login data schema."""

    email: EmailStr
    password: str


class DictationInput(BaseModel):
    """Schema for dictation input."""

    user_id: int
    audio: bytes


class DictationsBase(BaseModel):
    """Base schema for Dictations data."""

    user_id: int
    text: str
    formatted_text: str


class DictationsCreate(DictationsBase):
    """Schema for creating a new dictation."""


class DictationFormatInput(BaseModel):
    """Schema for formatting dictation with preferences."""

    transcript: str
    preferences: list[str]


class DictationsCreateResponse(DictationsBase):
    """Schema for DictationsCreateResponse data."""

    model_config = ConfigDict(from_attributes=True)
    id: int


class UserEditsInput(BaseModel):
    """Base schema for UserEdits data."""

    user_id: int
    original_text: str
    edited_text: str


class UserPreferencesCreate(BaseModel):
    """Base schema for UserPreferences data."""

    user_id: int
    user_edits_id: int
    rules: str | None


class UserPreferencesResponse(UserPreferencesCreate):
    """Schema for UserPreferencesResponse data."""

    model_config = ConfigDict(from_attributes=True)
    id: int | None
