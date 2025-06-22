from typing import Optional, List
import streamlit as st


class SessionManager:
    """Manages Streamlit session state."""
    
    @staticmethod
    def init_session_state() -> None:
        """Initialize session state variables if they don't exist."""
        defaults = {
            "jwt_token": None,
            "page": "auth",
            "auth_mode": "login",
            "transcript": "",
            "edited_transcript": "",
            "formatted_transcript": "",
            "dictation_id": None,
            "user_preferences": [],
            "error_message": None,
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def navigate_to_auth():
        """Switch to authentication page."""
        st.session_state.page = "auth"
    
    @staticmethod
    def navigate_to_function():
        """Switch to function page."""
        st.session_state.page = "function"
    
    @staticmethod
    def switch_to_login():
        """Switch to login mode in auth page."""
        st.session_state.auth_mode = "login"
    
    @staticmethod
    def switch_to_signup():
        """Switch to signup mode in auth page."""
        st.session_state.auth_mode = "signup"
    
    @staticmethod
    def set_error(message: str):
        """Set error message in session state."""
        st.session_state.error_message = message
    
    @staticmethod
    def clear_error():
        """Clear error message from session state."""
        st.session_state.error_message = None
    
    @staticmethod
    def logout():
        """Log out the user by clearing session state."""
        reset_keys = [
            "jwt_token", "transcript", "edited_transcript", 
            "formatted_transcript", "user_preferences", "error_message"
        ]
        
        for key in reset_keys:
            st.session_state[key] = None if key != "user_preferences" else []
        
        st.session_state.page = "auth"
        st.session_state.auth_mode = "login"
    
    @staticmethod
    def set_transcription_data(result: dict):
        """Set transcription data in session state."""
        st.session_state.transcript = result.get("text", "")
        st.session_state.edited_transcript = result.get("text", "")
        st.session_state.formatted_transcript = result.get("formatted_text", "")
        st.session_state.dictation_id = result.get("id", "")
    
    @staticmethod
    def clear_transcription_data():
        """Clear all transcription data."""
        st.session_state.transcript = ""
        st.session_state.edited_transcript = ""
        st.session_state.formatted_transcript = ""
        st.session_state.user_preferences = []
    
    @staticmethod
    def get_jwt_token() -> Optional[str]:
        """Get JWT token from session state."""
        return st.session_state.get("jwt_token")
    
    @staticmethod
    def set_user_preferences(preferences: List[str]):
        """Set user preferences in session state."""
        st.session_state.user_preferences = preferences