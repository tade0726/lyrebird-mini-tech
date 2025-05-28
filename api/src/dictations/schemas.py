from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from sqlalchemy import Column, Integer
from fastapi import UploadFile

# Dictations


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
    transcript: str
    preferences: list[str]


class DictationsCreateResponse(DictationsBase):
    """Schema for DictationsCreateResponse data.

    ConfigDict: it allows object data acccessed by attributes
    via: https://docs.pydantic.dev/latest/api/config/?query=ConfigDict#pydantic.config.ConfigDict.from_attributes
    """

    model_config = ConfigDict(from_attributes=True)
    id: int


# Preferences / edit


class UserEditsInput(BaseModel):
    """Base schema for UserEdits data."""

    user_id: int
    original_text: str
    edited_text: str


class UserPreferencesCreate(BaseModel):
    """Base schema for UserPreferences data."""

    user_id: int
    user_edits_id: int
    rules: str


class UserPreferencesResponse(UserPreferencesCreate):
    """Schema for UserPreferencesResponse data."""

    model_config = ConfigDict(from_attributes=True)
    id: int | None
