import streamlit as st

from session_manager import SessionManager
from ui_components import UIComponents
from error_handler import ErrorHandler


class LyrebirdPages:
    """Main page handlers for the Lyrebird application."""

    def __init__(self):
        self.ui_components = UIComponents()
        self.session_manager = SessionManager()
        self.error_handler = ErrorHandler()

    def auth_page(self) -> None:
        """Display the authentication page with login and signup options."""
        st.title("🎙️ Lyrebird")
        st.subheader("Audio Transcription Solution")

        self.ui_components.render_auth_toggle()
        self.ui_components.render_error_message()

        if st.session_state.auth_mode == "login":
            self.ui_components.render_login_form()
        else:
            self.ui_components.render_signup_form()

    def function_page(self) -> None:
        """Display main functionality page with audio recording and transcript editing."""
        st.title("🎙️ Lyrebird Audio Transcription")

        with st.sidebar:
            st.info("Logged in successfully")
            if st.button("Logout", key="logout_button", use_container_width=True):
                self.session_manager.logout()
                st.rerun()

            self.ui_components.render_sidebar_preferences()
            self.ui_components.render_help_section()

        tab1, tab2 = st.tabs(["📝 Record Audio", "📁 Upload Audio"])

        with tab1:
            self.ui_components.render_audio_recorder()

        with tab2:
            self.ui_components.render_audio_uploader()

        self.ui_components.render_transcript_section()


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Lyrebird Transcription",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    session_manager = SessionManager()
    session_manager.init_session_state()

    pages = LyrebirdPages()

    if st.session_state.jwt_token is None:
        pages.auth_page()
    else:
        pages.function_page()


if __name__ == "__main__":
    main()
