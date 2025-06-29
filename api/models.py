from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from api.database import Base


class UserModel(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    dictations = relationship("DictationsModel", back_populates="user")
    user_edits = relationship("UserEditsModel", back_populates="user")
    user_preferences = relationship("UserPreferencesModel", back_populates="user")


class DictationsModel(Base):
    """Dictation model for database"""

    __tablename__ = "dictations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    formatted_text = Column(Text, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("UserModel", back_populates="dictations")

    def __repr__(self):
        return f"<Dictation(id={self.id}, user_id={self.user_id})>"


class UserEditsModel(Base):
    """UserEdits model for database"""

    __tablename__ = "user_edits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    edited_text = Column(Text, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("UserModel", back_populates="user_edits")
    user_preferences = relationship(
        "UserPreferencesModel", back_populates="user_edit", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserEdit(id={self.id}, user_id={self.user_id})>"


class UserPreferencesModel(Base):
    """UserPreferences model for database"""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_edits_id = Column(
        Integer, ForeignKey("user_edits.id"), nullable=False, index=True
    )
    rules = Column(Text, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("UserModel", back_populates="user_preferences")
    user_edit = relationship("UserEditsModel", back_populates="user_preferences")

    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id={self.user_id})>"
