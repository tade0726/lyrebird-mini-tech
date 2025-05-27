import os
import tempfile
from typing import Dict, Optional, Union, List, Any

import requests
import pyperclip
import streamlit as st
from streamlit_mic_recorder import mic_recorder

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Configuration
API_BASE_URL = os.environ.get(
    "API_BASE_URL", "http://localhost:8000"
)  # Read from environment variable with fallback

# ============================================================================
# API ENDPOINTS
# ============================================================================

# Authentication Endpoints
AUTH_LOGIN_ENDPOINT = f"{API_BASE_URL}/auth/login"  # POST with form data
AUTH_REGISTER_ENDPOINT = f"{API_BASE_URL}/auth/register"  # POST with JSON

# Dictation Endpoints
DICTATION_ENDPOINT = f"{API_BASE_URL}/dictations"  # POST with multipart/form-data
PREFERENCE_EXTRACT_ENDPOINT = (
    f"{API_BASE_URL}/dictations/preference_extract"  # POST with JSON
)
PREFERENCES_ENDPOINT = f"{API_BASE_URL}/dictations/preferences"  # GET endpoint to fetch all user preferences

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================


def init_session_state() -> None:
    """Initialize session state variables if they don't exist."""
    # Authentication state
    if "jwt_token" not in st.session_state:
        st.session_state.jwt_token = None

    # Page navigation
    if "page" not in st.session_state:
        st.session_state.page = "auth"  # Options: auth, function

    # Auth page mode
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"  # Options: login, signup

    # Transcript data
    if "transcript" not in st.session_state:
        st.session_state.transcript = ""
    if "edited_transcript" not in st.session_state:
        st.session_state.edited_transcript = ""
    if "formatted_transcript" not in st.session_state:
        st.session_state.formatted_transcript = ""
    if "dictation_id" not in st.session_state:
        st.session_state.dictation_id = None
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = []

    # Error handling
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


# ============================================================================
# PAGE NAVIGATION FUNCTIONS
# ============================================================================


def navigate_to_auth():
    """Switch to authentication page."""
    st.session_state.page = "auth"


def navigate_to_function():
    """Switch to function page."""
    st.session_state.page = "function"


def switch_to_login():
    """Switch to login mode in auth page."""
    st.session_state.auth_mode = "login"


def switch_to_signup():
    """Switch to signup mode in auth page."""
    st.session_state.auth_mode = "signup"


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================


def login(username: str, password: str) -> bool:
    """Authenticate user with the API and store JWT token in session state.

    Args:
        username: User's email address for login
        password: User's password

    Returns:
        True if login successful, False otherwise
    """
    try:
        # Using form data as specified in the API requirements
        response = requests.post(
            AUTH_LOGIN_ENDPOINT,
            data={
                "username": username,
                "password": password,
            },  # Form data format per API spec
        )

        # Process response
        if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
            data = response.json()
            st.session_state.jwt_token = data.get("access_token")
            st.session_state.error_message = None
            navigate_to_function()  # Automatically navigate to function page after login
            return True
        else:
            st.session_state.error_message = f"Login failed: {response.text}"
            return False
    except Exception as e:
        st.session_state.error_message = f"Login error: {str(e)}"
        return False


def register(email: str, password: str) -> bool:
    """Register a new user with the API.

    Args:
        email: User's email address for registration
        password: User's password

    Returns:
        True if registration successful, False otherwise
    """
    try:
        # Using JSON data as specified in the API requirements
        response = requests.post(
            AUTH_REGISTER_ENDPOINT,
            json={"email": email, "password": password},  # JSON format per API spec
        )

        # Process response
        if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
            st.session_state.error_message = None
            # Switch to login mode after successful registration
            st.session_state.auth_mode = "login"
            return True
        else:
            st.session_state.error_message = f"Registration failed: {response.text}"
            return False
    except Exception as e:
        st.session_state.error_message = f"Registration error: {str(e)}"
        return False


def logout() -> None:
    """Log out the user by clearing session state."""
    # Simple reset of critical session variables
    st.session_state.jwt_token = None
    st.session_state.page = "auth"
    st.session_state.auth_mode = "login"
    st.session_state.transcript = ""
    st.session_state.edited_transcript = ""
    st.session_state.formatted_transcript = ""
    st.session_state.user_preferences = None
    st.session_state.error_message = None


# ============================================================================
# API INTERACTION FUNCTIONS
# ============================================================================


def send_audio_to_dictation(
    audio_data: bytes, file_extension: str = ".wav"
) -> Dict[str, Any]:
    """Send audio file to the dictation API endpoint for transcription.

    Args:
        audio_data: Binary audio data to be transcribed
        file_extension: The file extension for the audio file (default: .wav)

    Returns:
        Dictionary containing transcription data or error message
    """
    try:
        # Make sure we have a valid extension (with the dot)
        if not file_extension.startswith("."):
            file_extension = f".{file_extension}"

        # Ensure we're using a supported format
        valid_extensions = [".wav", ".mp3", ".mpeg", ".mp4", ".ogg"]
        if file_extension.lower() not in valid_extensions:
            file_extension = ".wav"  # Default to wav if unsupported

        # Create a temporary file to hold the audio data
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(audio_data)

        # Prepare headers with JWT token for authentication
        headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}

        # Send multipart/form-data request with audio file
        with open(temp_file_path, "rb") as audio_file:
            # Set the appropriate content type based on file extension
            content_type = None
            if file_extension.lower() in [".mp3", ".mpeg"]:
                content_type = "audio/mpeg"
            elif file_extension.lower() == ".wav":
                content_type = "audio/wav"
            elif file_extension.lower() == ".ogg":
                content_type = "audio/ogg"
            elif file_extension.lower() == ".mp4":
                content_type = "audio/mp4"

            # Create the files dictionary with proper content type
            files = {"audio": (f"audio{file_extension}", audio_file, content_type)}

            response = requests.post(DICTATION_ENDPOINT, headers=headers, files=files)

        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass  # Ignore cleanup errors

        # Process the response
        if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
            return {
                "success": True,
                **response.json(),  # Include all data from the API response
            }
        else:
            return {
                "success": False,
                "error": f"API Error ({response.status_code}): {response.text}",
            }

    except Exception as e:
        return {"success": False, "error": f"Error sending audio: {str(e)}"}


def submit_edit(original_text: str, edited_text: str) -> Optional[Dict[str, Any]]:
    """Submit original and edited text to extract user preferences.

    Args:
        original_text: The original transcribed text
        edited_text: The user-edited version of the text

    Returns:
        Dictionary containing preference data or None if an error occurred
    """
    try:
        # Prepare headers with JWT token for authentication
        headers = {
            "Authorization": f"Bearer {st.session_state.jwt_token}",
        }

        # Send the request with query parameters
        response = requests.post(
            PREFERENCE_EXTRACT_ENDPOINT,
            headers=headers,
            params={"original_text": original_text, "edited_text": edited_text},
        )

        # Process response
        if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
            result = response.json()
            # Extract preferences and save them if available
            if "preferences" in result and result["preferences"]:
                st.session_state.user_preferences = result["preferences"]
            return result
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None

    except Exception as e:
        st.error(f"Error submitting edit: {str(e)}")
        return None


def fetch_user_preferences() -> List[str]:
    """Fetch user preferences from the API.

    Returns:
        List of user preference strings
    """
    try:
        # Prepare headers with JWT token for authentication
        headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}

        # Send the request to the proper endpoint
        try:
            response = requests.get(PREFERENCES_ENDPOINT, headers=headers)
        except Exception as req_err:
            st.error(f"Request error: {str(req_err)}")
            return []

        # Process response
        if response.status_code in [200, 201]:
            try:
                preferences_data = response.json()

                # Check if we got an empty response
                if not preferences_data:
                    return []

                # Extract all preference strings from the response
                all_preferences = []

                # Based on the API structure, we need to extract preferences correctly
                if isinstance(preferences_data, list):
                    for pref_obj in preferences_data:
                        if isinstance(pref_obj, dict) and "preferences" in pref_obj:
                            prefs = pref_obj.get("preferences", [])
                            if isinstance(prefs, list):
                                all_preferences.extend(prefs)
                            elif isinstance(prefs, str):
                                all_preferences.append(prefs)

                # If we received a single object instead of a list
                elif (
                    isinstance(preferences_data, dict)
                    and "preferences" in preferences_data
                ):
                    prefs = preferences_data.get("preferences", [])
                    if isinstance(prefs, list):
                        all_preferences.extend(prefs)
                    elif isinstance(prefs, str):
                        all_preferences.append(prefs)

                # Remove duplicates while preserving order
                unique_preferences = []
                for pref in all_preferences:
                    if pref not in unique_preferences and pref.strip():
                        unique_preferences.append(pref)

                return unique_preferences
            except Exception as parse_err:
                st.error(f"Error parsing preferences: {str(parse_err)}")
                st.error(f"Raw response: {response.text}")
                return []
        else:
            st.error(
                f"API returned status code {response.status_code}: {response.text}"
            )
            return []

    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return []


# ============================================================================
# UI COMPONENTS - AUTHENTICATION PAGE
# ============================================================================


def auth_page() -> None:
    """Display the authentication page with login and signup options."""
    st.title("🎙️ Lyrebird")
    st.subheader("Audio Transcription Solution")

    # Toggle buttons to switch between login and signup modes
    col1, col2 = st.columns(2)
    with col1:
        login_button = st.button(
            "Login",
            use_container_width=True,
            type="primary" if st.session_state.auth_mode == "login" else "secondary",
        )
        if login_button:
            switch_to_login()

    with col2:
        signup_button = st.button(
            "Sign Up",
            use_container_width=True,
            type="primary" if st.session_state.auth_mode == "signup" else "secondary",
        )
        if signup_button:
            switch_to_signup()

    # Display error message if any
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.session_state.error_message = None  # Clear after showing

    # Login form
    if st.session_state.auth_mode == "login":
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if email and password:
                    login(email, password)
                else:
                    st.error("Please enter both email and password")

    # Signup form
    else:  # signup mode
        with st.form("signup_form"):
            st.subheader("Create an Account")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )
            submit = st.form_submit_button("Sign Up", use_container_width=True)

            if submit:
                if not email or not password or not confirm_password:
                    st.error("Please fill out all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success = register(email, password)
                    if success:
                        st.success("Account created successfully! Please log in.")
                        # Will automatically switch to login mode due to the register function


# ============================================================================
# UI COMPONENTS - MAIN FUNCTIONALITY PAGE
# ============================================================================


def function_page() -> None:
    """Display main functionality page with audio recording and transcript editing."""
    # Page header
    st.title("🎙️ Lyrebird Audio Transcription")

    # User info and logout in sidebar
    with st.sidebar:
        st.info("Logged in successfully")
        if st.button("Logout", key="logout_button", use_container_width=True):
            logout()
            st.rerun()  # Force a page refresh after logout

        # Display user preferences section
        st.markdown("### ✨ Your Writing Preferences")

        # Fetch preferences for display
        with st.spinner("Loading your preferences..."):
            headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
            try:
                response = requests.get(PREFERENCES_ENDPOINT, headers=headers)

                if response.status_code == 200:
                    try:
                        raw_data = response.json()

                        # Process the response - looking for the 'rules' field in the API response
                        preferences = []
                        if isinstance(raw_data, list):
                            for item in raw_data:
                                if isinstance(item, dict) and "rules" in item:
                                    # Rules might be a string in this API structure
                                    if (
                                        isinstance(item["rules"], str)
                                        and item["rules"].strip()
                                    ):
                                        preferences.append(item["rules"])
                                    elif isinstance(item["rules"], list):
                                        preferences.extend(item["rules"])

                        # Show preferences if found
                        if preferences:
                            st.session_state.user_preferences = preferences

                            # Create a more visually appealing display for preferences
                            for i, pref in enumerate(preferences):
                                with st.container():
                                    st.markdown(
                                        f"""<div style='background-color: #f0f7ff; padding: 10px; 
                                                border-radius: 5px; margin-bottom: 8px; border-left: 3px solid #4361ee;'>
                                                <span style='color: #1e3a8a; font-weight: 500;'>{pref}</span>
                                                </div>""",
                                        unsafe_allow_html=True,
                                    )
                        else:
                            st.info(
                                "No preferences found yet. Submit edits to generate preferences."
                            )
                    except Exception:
                        st.info("Unable to load preferences. Please try again later.")
                else:
                    st.info("Unable to load preferences. Please try again later.")
            except Exception:
                st.info(
                    "Unable to connect to the server. Please check your connection."
                )

        # Add refresh button for preferences with a more appealing design
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄", key="refresh_prefs", help="Refresh your preferences"):
                with st.spinner("Refreshing..."):
                    # Direct API call to refresh preferences
                    headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
                    try:
                        response = requests.get(PREFERENCES_ENDPOINT, headers=headers)
                        if response.status_code == 200:
                            raw_data = response.json()
                            preferences = []
                            if isinstance(raw_data, list):
                                for item in raw_data:
                                    if isinstance(item, dict) and "rules" in item:
                                        if (
                                            isinstance(item["rules"], str)
                                            and item["rules"].strip()
                                        ):
                                            preferences.append(item["rules"])
                                        elif isinstance(item["rules"], list):
                                            preferences.extend(item["rules"])
                            st.session_state.user_preferences = preferences
                            st.rerun()
                    except Exception:
                        pass

        # Help information
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

    # Main content area with tabs
    tab1, tab2 = st.tabs(["📝 Record Audio", "📁 Upload Audio"])

    # Tab 1: Audio Recording
    with tab1:
        st.subheader("Record Audio")
        st.write(
            "Click to start recording audio, then click again to stop and transcribe."
        )

        # Audio recorder component with styling
        st.markdown("#### 🎤 Record")
        audio_dict = mic_recorder(
            start_prompt="Start recording",
            stop_prompt="Stop & transcribe",
            key="recorder",
            just_once=True,  # Return once, then reset
            use_container_width=True,
        )

        # Process audio recording if available
        if audio_dict:
            audio_bytes = audio_dict["bytes"]

            with st.spinner("Transcribing audio..."):
                # Mic recorder returns WAV format
                result = send_audio_to_dictation(audio_bytes, file_extension=".wav")

                if result["success"]:
                    # Store the transcription results in session state
                    st.session_state.transcript = result.get("text", "")
                    st.session_state.edited_transcript = result.get("text", "")
                    st.session_state.formatted_transcript = result.get(
                        "formatted_text", ""
                    )
                    st.session_state.dictation_id = result.get("id", "")

                    # Show success message only
                    st.success("Audio transcribed successfully!")
                    # Force a rerun to update the transcript container
                    st.rerun()
                else:
                    st.error(result["error"])

    # Tab 2: Audio Upload
    with tab2:
        st.subheader("Upload Audio File")
        st.write("Select an audio file from your device to transcribe.")

        # File uploader with clear instructions
        uploaded_file = st.file_uploader(
            "Supported formats: WAV, MP3, M4A, OGG",
            type=["wav", "mp3", "mpga", "m4a", "ogg"],
        )

        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            # Display audio player if possible
            st.audio(uploaded_file)

            # Transcribe button for uploaded file
            if st.button("Transcribe Audio"):
                # Get file bytes
                audio_bytes = uploaded_file.getvalue()

                # Extract file extension from the uploaded file's name
                filename = uploaded_file.name
                file_extension = os.path.splitext(filename)[1].lower()

                with st.spinner("Transcribing uploaded audio..."):
                    result = send_audio_to_dictation(
                        audio_bytes, file_extension=file_extension
                    )

                    if result["success"]:
                        # Store the transcription results in session state
                        st.session_state.transcript = result.get("text", "")
                        st.session_state.edited_transcript = result.get("text", "")
                        st.session_state.formatted_transcript = result.get(
                            "formatted_text", ""
                        )
                        st.session_state.dictation_id = result.get("id", "")

                        # Show success message
                        st.success("Audio transcribed successfully!")
                        # Force a rerun to update the transcript container
                        st.rerun()
                    else:
                        # Show error message
                        st.error(
                            result.get(
                                "error",
                                "An unknown error occurred during transcription.",
                            )
                        )

    # Transcript section (shown below the tabs)
    with st.container():
        st.markdown("---")
        st.subheader("📄 Formatted Transcript")

        # Check for transcription data
        has_transcript = bool(
            st.session_state.transcript or st.session_state.edited_transcript
        )
        has_formatted = bool(st.session_state.formatted_transcript)

        # Display transcript content
        if has_formatted:
            # Allow editing the formatted transcript directly - single editable box
            edited_formatted = st.text_area(
                "Edit formatted transcript if needed:",
                value=st.session_state.formatted_transcript,
                height=400,
                key="formatted_edit_area",
            )

            # Update the edited transcript if changed
            if edited_formatted != st.session_state.formatted_transcript:
                st.session_state.edited_transcript = edited_formatted

            # Action buttons in columns for better layout
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.button(
                    "📋 Copy", disabled=not edited_formatted, use_container_width=True
                ):
                    pyperclip.copy(edited_formatted)
                    st.success("Copied to clipboard!")

            with col2:
                if st.button(
                    "📤 Submit",
                    disabled=not st.session_state.transcript,
                    use_container_width=True,
                ):
                    with st.spinner("Analyzing preferences..."):
                        result = submit_edit(
                            st.session_state.transcript, edited_formatted
                        )
                        if result:
                            # Refresh preferences from the API after successful submission
                            st.session_state.user_preferences = fetch_user_preferences()
                            st.success("Preferences extracted and updated!")
                            st.rerun()  # Refresh to show updated preferences in sidebar
                        else:
                            st.error("Failed to extract preferences")

            with col3:
                if st.button(
                    "🗑️ Clear",
                    disabled=not st.session_state.formatted_transcript,
                    use_container_width=True,
                ):
                    st.session_state.transcript = ""
                    st.session_state.edited_transcript = ""
                    st.session_state.formatted_transcript = ""
                    st.session_state.user_preferences = None
                    st.rerun()
        elif has_transcript and not has_formatted:
            # Show a message if we have transcript but no formatted text
            st.info(
                "Original transcript available but no formatted version was provided by the API."
            )
            st.text_area(
                "Original Transcript",
                value=st.session_state.transcript,
                height=200,
                disabled=True,
            )
        else:
            # No transcript available yet
            st.info("Record or upload audio to see your transcript here.")


# ============================================================================
# MAIN APPLICATION
# ============================================================================


def main():
    """Main application entry point."""
    # Set page configuration
    st.set_page_config(
        page_title="Lyrebird Transcription",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    init_session_state()

    # Route to the appropriate page based on session state
    if st.session_state.jwt_token is None:
        # User is not authenticated, show login/signup page
        auth_page()
    else:
        # User is authenticated, show function page
        function_page()


if __name__ == "__main__":
    main()
