import os
import tempfile
from typing import Dict, Optional, List, Any

import requests
import streamlit as st

from config import config
from session_manager import SessionManager


class APIClient:
    """Handles all API interactions."""

    def __init__(self):
        self.session_manager = SessionManager()

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with JWT token."""
        token = self.session_manager.get_jwt_token()
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response consistently."""
        if response.status_code in [200, 201]:
            return {"success": True, **response.json()}
        else:
            return {
                "success": False,
                "error": f"API Error ({response.status_code}): {response.text}",
            }

    def login(self, username: str, password: str) -> bool:
        """Authenticate user with the API."""
        try:
            response = requests.post(
                config.auth_login_endpoint,
                data={"username": username, "password": password},
            )

            if response.status_code in [200, 201]:
                data = response.json()
                st.session_state.jwt_token = data.get("access_token")
                self.session_manager.clear_error()
                self.session_manager.navigate_to_function()
                return True
            else:
                self.session_manager.set_error(f"Login failed: {response.text}")
                return False
        except Exception as e:
            self.session_manager.set_error(f"Login error: {str(e)}")
            return False

    def register(self, email: str, password: str) -> bool:
        """Register a new user with the API."""
        try:
            response = requests.post(
                config.auth_register_endpoint,
                json={"email": email, "password": password},
            )

            if response.status_code in [200, 201]:
                self.session_manager.clear_error()
                self.session_manager.switch_to_login()
                return True
            else:
                self.session_manager.set_error(f"Registration failed: {response.text}")
                return False
        except Exception as e:
            self.session_manager.set_error(f"Registration error: {str(e)}")
            return False

    def send_audio_to_dictation(
        self, audio_data: bytes, file_extension: str = ".wav"
    ) -> Dict[str, Any]:
        """Send audio file to the dictation API endpoint for transcription."""
        try:
            if not file_extension.startswith("."):
                file_extension = f".{file_extension}"

            valid_extensions = [".wav", ".mp3", ".mpeg", ".mp4", ".ogg"]
            if file_extension.lower() not in valid_extensions:
                file_extension = ".wav"

            with tempfile.NamedTemporaryFile(
                suffix=file_extension, delete=False
            ) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(audio_data)

            headers = self._get_headers()

            with open(temp_file_path, "rb") as audio_file:
                content_type = self._get_content_type(file_extension)
                files = {"audio": (f"audio{file_extension}", audio_file, content_type)}
                response = requests.post(
                    config.dictation_endpoint, headers=headers, files=files
                )

            try:
                os.unlink(temp_file_path)
            except:
                pass

            return self._handle_response(response)

        except Exception as e:
            return {"success": False, "error": f"Error sending audio: {str(e)}"}

    def _get_content_type(self, file_extension: str) -> Optional[str]:
        """Get content type based on file extension."""
        content_types = {
            ".mp3": "audio/mpeg",
            ".mpeg": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".mp4": "audio/mp4",
        }
        return content_types.get(file_extension.lower())

    def submit_edit(
        self, original_text: str, edited_text: str
    ) -> Optional[Dict[str, Any]]:
        """Submit original and edited text to extract user preferences."""
        try:
            headers = self._get_headers()
            response = requests.post(
                config.preference_extract_endpoint,
                headers=headers,
                params={"original_text": original_text, "edited_text": edited_text},
            )

            if response.status_code in [200, 201]:
                result = response.json()
                if "preferences" in result and result["preferences"]:
                    self.session_manager.set_user_preferences(result["preferences"])
                return result
            else:
                return None
        except Exception:
            return None

    def fetch_user_preferences(self) -> List[str]:
        """Fetch user preferences from the API."""
        try:
            headers = self._get_headers()
            response = requests.get(config.preferences_endpoint, headers=headers)

            if response.status_code in [200, 201]:
                preferences_data = response.json()

                if not preferences_data:
                    return []

                all_preferences = []

                if isinstance(preferences_data, list):
                    for pref_obj in preferences_data:
                        if isinstance(pref_obj, dict) and "rules" in pref_obj:
                            rules = pref_obj.get("rules", [])
                            if isinstance(rules, str) and rules.strip():
                                all_preferences.append(rules)
                            elif isinstance(rules, list):
                                all_preferences.extend(rules)
                elif isinstance(preferences_data, dict) and "rules" in preferences_data:
                    rules = preferences_data.get("rules", [])
                    if isinstance(rules, str) and rules.strip():
                        all_preferences.append(rules)
                    elif isinstance(rules, list):
                        all_preferences.extend(rules)

                # Remove duplicates while preserving order
                unique_preferences = []
                for pref in all_preferences:
                    if pref not in unique_preferences and pref.strip():
                        unique_preferences.append(pref)

                return unique_preferences

            return []
        except Exception:
            return []
