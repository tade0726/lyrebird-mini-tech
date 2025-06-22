import os
from typing import Dict, Any

import streamlit as st
import pyperclip
from streamlit_mic_recorder import mic_recorder

from api_client import APIClient
from session_manager import SessionManager


class UIComponents:
    """Reusable UI components for the Streamlit app."""

    def __init__(self):
        self.api_client = APIClient()
        self.session_manager = SessionManager()

    def render_error_message(self):
        """Display error message if present."""
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
            self.session_manager.clear_error()

    def render_auth_toggle(self):
        """Render login/signup toggle buttons."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Login",
                use_container_width=True,
                type=(
                    "primary" if st.session_state.auth_mode == "login" else "secondary"
                ),
            ):
                self.session_manager.switch_to_login()

        with col2:
            if st.button(
                "Sign Up",
                use_container_width=True,
                type=(
                    "primary" if st.session_state.auth_mode == "signup" else "secondary"
                ),
            ):
                self.session_manager.switch_to_signup()

    def render_login_form(self):
        """Render login form."""
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.form_submit_button("Login", use_container_width=True):
                if email and password:
                    self.api_client.login(email, password)
                else:
                    st.error("Please enter both email and password")

    def render_signup_form(self):
        """Render signup form."""
        with st.form("signup_form"):
            st.subheader("Create an Account")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )

            if st.form_submit_button("Sign Up", use_container_width=True):
                if not email or not password or not confirm_password:
                    st.error("Please fill out all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    if self.api_client.register(email, password):
                        st.success("Account created successfully! Please log in.")

    def render_sidebar_preferences(self):
        """Render user preferences in sidebar."""
        st.markdown("### ✨ Your Writing Preferences")

        with st.spinner("Loading your preferences..."):
            preferences = self.api_client.fetch_user_preferences()

            if preferences:
                self.session_manager.set_user_preferences(preferences)
                for pref in preferences:
                    st.markdown(self._format_preference(pref), unsafe_allow_html=True)
            else:
                st.info(
                    "No preferences found yet. Submit edits to generate preferences."
                )

        # Refresh button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄", key="refresh_prefs", help="Refresh your preferences"):
                self._refresh_preferences()

    def _format_preference(self, preference: str) -> str:
        """Format preference text with styling."""
        return f"""
        <div style='background-color: #f0f7ff; padding: 10px; 
                    border-radius: 5px; margin-bottom: 8px; border-left: 3px solid #4361ee;'>
            <span style='color: #1e3a8a; font-weight: 500;'>{preference}</span>
        </div>
        """

    def _refresh_preferences(self):
        """Refresh user preferences."""
        with st.spinner("Refreshing..."):
            preferences = self.api_client.fetch_user_preferences()
            self.session_manager.set_user_preferences(preferences)
            st.rerun()

    def render_help_section(self):
        """Render help information."""
        with st.expander("ℹ️ How to use"):
            st.markdown(
                """
            **Recording Audio:**
            1. Go to the Record Audio tab
            2. Click the microphone button to start recording
            3. Click again to stop and transcribe
            
            **Uploading Audio:**
            1. Go to the Upload Audio tab
            2. Select an audio file from your device
            
            **Working with Transcripts:**
            - View the formatted transcript
            - Use the Copy button to copy the text
            - Use Submit to analyze your preferences
            - Clear to reset the transcript
            """
            )

    def render_audio_recorder(self):
        """Render audio recorder component."""
        st.subheader("Record Audio")
        st.write(
            "Click to start recording audio, then click again to stop and transcribe."
        )

        st.markdown("#### 🎤 Record")
        audio_dict = mic_recorder(
            start_prompt="Start recording",
            stop_prompt="Stop & transcribe",
            key="recorder",
            just_once=True,
            use_container_width=True,
        )

        if audio_dict:
            self._process_recorded_audio(audio_dict["bytes"])

    def render_audio_uploader(self):
        """Render audio file uploader."""
        st.subheader("Upload Audio File")
        st.write("Select an audio file from your device to transcribe.")

        uploaded_file = st.file_uploader(
            "Supported formats: WAV, MP3, M4A, OGG",
            type=["wav", "mp3", "mpga", "m4a", "ogg"],
        )

        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            st.audio(uploaded_file)

            if st.button("Transcribe Audio"):
                self._process_uploaded_audio(uploaded_file)

    def _process_recorded_audio(self, audio_bytes: bytes):
        """Process recorded audio data."""
        with st.spinner("Transcribing audio..."):
            result = self.api_client.send_audio_to_dictation(
                audio_bytes, file_extension=".wav"
            )

            if result["success"]:
                self.session_manager.set_transcription_data(result)
                st.success("Audio transcribed successfully!")
                st.rerun()
            else:
                st.error(result["error"])

    def _process_uploaded_audio(self, uploaded_file):
        """Process uploaded audio file."""
        audio_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        file_extension = os.path.splitext(filename)[1].lower()

        with st.spinner("Transcribing uploaded audio..."):
            result = self.api_client.send_audio_to_dictation(
                audio_bytes, file_extension=file_extension
            )

            if result["success"]:
                self.session_manager.set_transcription_data(result)
                st.success("Audio transcribed successfully!")
                st.rerun()
            else:
                st.error(
                    result.get(
                        "error", "An unknown error occurred during transcription."
                    )
                )

    def render_transcript_section(self):
        """Render transcript editing and action buttons."""
        st.markdown("---")
        st.subheader("📄 Formatted Transcript")

        has_formatted = bool(st.session_state.formatted_transcript)
        has_transcript = bool(
            st.session_state.transcript or st.session_state.edited_transcript
        )

        if has_formatted:
            self._render_editable_transcript()
        elif has_transcript and not has_formatted:
            self._render_original_transcript_only()
        else:
            st.info("Record or upload audio to see your transcript here.")

    def _render_editable_transcript(self):
        """Render editable transcript with action buttons."""
        edited_formatted = st.text_area(
            "Edit formatted transcript if needed:",
            value=st.session_state.formatted_transcript,
            height=400,
            key="formatted_edit_area",
        )

        if edited_formatted != st.session_state.formatted_transcript:
            st.session_state.edited_transcript = edited_formatted

        self._render_action_buttons(edited_formatted)

    def _render_original_transcript_only(self):
        """Render original transcript when no formatted version is available."""
        st.info(
            "Original transcript available but no formatted version was provided by the API."
        )
        st.text_area(
            "Original Transcript",
            value=st.session_state.transcript,
            height=200,
            disabled=True,
        )

    def _render_action_buttons(self, edited_text: str):
        """Render copy, submit, and clear buttons."""
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("📋 Copy", disabled=not edited_text, use_container_width=True):
                pyperclip.copy(edited_text)
                st.success("Copied to clipboard!")

        with col2:
            if st.button(
                "📤 Submit",
                disabled=not st.session_state.transcript,
                use_container_width=True,
            ):
                self._handle_submit_edit(edited_text)

        with col3:
            if st.button(
                "🗑️ Clear",
                disabled=not st.session_state.formatted_transcript,
                use_container_width=True,
            ):
                self.session_manager.clear_transcription_data()
                st.rerun()

    def _handle_submit_edit(self, edited_text: str):
        """Handle submit edit action."""
        with st.spinner("Analyzing preferences..."):
            result = self.api_client.submit_edit(
                st.session_state.transcript, edited_text
            )

            if result:
                preferences = self.api_client.fetch_user_preferences()
                self.session_manager.set_user_preferences(preferences)
                st.success("Preferences extracted and updated!")
                st.rerun()
            else:
                st.error("Failed to extract preferences")
