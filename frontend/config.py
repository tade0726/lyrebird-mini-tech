import os
from dotenv import load_dotenv

load_dotenv(".env")


class Config:
    """Application configuration."""

    API_BASE_URL = os.environ.get("API_BASE_URL")

    @property
    def auth_login_endpoint(self) -> str:
        return f"{self.API_BASE_URL}/auth/login"

    @property
    def auth_register_endpoint(self) -> str:
        return f"{self.API_BASE_URL}/auth/register"

    @property
    def dictation_endpoint(self) -> str:
        return f"{self.API_BASE_URL}/dictations"

    @property
    def preference_extract_endpoint(self) -> str:
        return f"{self.API_BASE_URL}/dictations/preference_extract"

    @property
    def preferences_endpoint(self) -> str:
        return f"{self.API_BASE_URL}/dictations/preferences"


config = Config()
