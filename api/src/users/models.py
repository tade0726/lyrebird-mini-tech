from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from api.core.database import Base


class UserModel(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    dictations = relationship("DictationsModel", back_populates="user")
    user_edits = relationship("UserEditsModel", back_populates="user")
    user_preferences = relationship("UserPreferencesModel", back_populates="user")
