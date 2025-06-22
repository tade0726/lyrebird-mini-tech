import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from io import BytesIO

from api.models import UserModel, DictationsModel, UserPreferencesModel


class TestDictationEndpoints:
    """Test dictation endpoints."""

    @patch("api.services.llm_service.LLMService.transcribe_audio")
    @patch("api.services.llm_service.LLMService.format_transcript")
    async def test_create_dictation_success(
        self,
        mock_format,
        mock_transcribe,
        client: AsyncClient,
        auth_headers: dict,
        sample_audio_data: bytes,
    ):
        """Test successful audio dictation."""
        # Mock LLM responses
        mock_transcribe.return_value = "This is a test transcription."
        mock_format.return_value = "**This is a formatted test transcription.**"

        # Create audio file
        audio_file = BytesIO(sample_audio_data)

        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("test.wav", audio_file, "audio/wav")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["text"] == "This is a test transcription."
        assert data["formatted_text"] == "**This is a formatted test transcription.**"
        assert "id" in data
        assert "user_id" in data

    async def test_create_dictation_unauthorized(
        self, client: AsyncClient, sample_audio_data: bytes
    ):
        """Test dictation without authentication."""
        audio_file = BytesIO(sample_audio_data)

        response = await client.post(
            "/dictations/", files={"audio": ("test.wav", audio_file, "audio/wav")}
        )

        assert response.status_code == 401

    async def test_create_dictation_invalid_file_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test dictation with invalid file type."""
        text_file = BytesIO(b"This is not an audio file")

        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("test.txt", text_file, "text/plain")},
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    async def test_create_dictation_file_too_large(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test dictation with file too large."""
        # Create a file larger than 10MB
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = BytesIO(large_data)

        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("large.wav", large_file, "audio/wav")},
        )

        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]

    async def test_create_dictation_no_file(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test dictation without file."""
        response = await client.post("/dictations/", headers=auth_headers)

        assert response.status_code == 422

    @patch("api.services.llm_service.LLMService.transcribe_audio")
    async def test_create_dictation_transcription_error(
        self,
        mock_transcribe,
        client: AsyncClient,
        auth_headers: dict,
        sample_audio_data: bytes,
    ):
        """Test dictation when transcription fails."""
        # Mock transcription failure
        mock_transcribe.side_effect = Exception("Transcription failed")

        audio_file = BytesIO(sample_audio_data)

        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("test.wav", audio_file, "audio/wav")},
        )

        assert response.status_code == 500
        assert "Failed to process" in response.json()["detail"]


class TestPreferenceEndpoints:
    """Test preference extraction endpoints."""

    @patch("api.services.llm_service.LLMService.extract_user_preferences")
    async def test_preference_extract_success(
        self, mock_extract, client: AsyncClient, auth_headers: dict
    ):
        """Test successful preference extraction."""
        # Mock preference extraction
        mock_extract.return_value = "The user prefers bullet points for lists."

        response = await client.post(
            "/dictations/preference_extract",
            headers=auth_headers,
            params={
                "original_text": "Original text here",
                "edited_text": "Edited text here with bullets",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rules"] == "The user prefers bullet points for lists."
        assert "user_id" in data
        assert "user_edits_id" in data

    @patch("api.services.llm_service.LLMService.extract_user_preferences")
    async def test_preference_extract_no_new_preference(
        self, mock_extract, client: AsyncClient, auth_headers: dict
    ):
        """Test preference extraction when no new preference found."""
        # Mock no new preference
        mock_extract.return_value = None

        response = await client.post(
            "/dictations/preference_extract",
            headers=auth_headers,
            params={
                "original_text": "Original text",
                "edited_text": "Same text basically",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rules"] is None
        assert data["id"] is None

    async def test_preference_extract_unauthorized(self, client: AsyncClient):
        """Test preference extraction without authentication."""
        response = await client.post(
            "/dictations/preference_extract",
            params={"original_text": "Original text", "edited_text": "Edited text"},
        )

        assert response.status_code == 401

    async def test_preference_extract_missing_params(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test preference extraction with missing parameters."""
        response = await client.post(
            "/dictations/preference_extract",
            headers=auth_headers,
            params={"original_text": "Only original text"},
        )

        assert response.status_code == 422

    async def test_get_user_preferences_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting user preferences when none exist."""
        response = await client.get("/dictations/preferences", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_get_user_preferences_with_data(
        self, client: AsyncClient, auth_headers: dict, test_db
    ):
        """Test getting user preferences with existing data."""
        # First extract a preference
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "The user prefers bullet points."

            await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={
                    "original_text": "Original text",
                    "edited_text": "• Edited text with bullets",
                },
            )

        # Now get preferences
        response = await client.get("/dictations/preferences", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rules"] == "The user prefers bullet points."

    async def test_get_user_preferences_unauthorized(self, client: AsyncClient):
        """Test getting preferences without authentication."""
        response = await client.get("/dictations/preferences")

        assert response.status_code == 401


class TestFileValidation:
    """Test file upload validation."""

    async def test_supported_audio_formats(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test various supported audio formats."""
        formats = [
            ("test.wav", "audio/wav"),
            ("test.mp3", "audio/mpeg"),
            ("test.mp4", "audio/mp4"),
            ("test.ogg", "audio/ogg"),
        ]

        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            with patch(
                "api.services.llm_service.LLMService.format_transcript"
            ) as mock_format:
                mock_transcribe.return_value = "Test transcription"
                mock_format.return_value = "Formatted test"

                for filename, content_type in formats:
                    audio_file = BytesIO(b"fake audio data")

                    response = await client.post(
                        "/dictations/",
                        headers=auth_headers,
                        files={"audio": (filename, audio_file, content_type)},
                    )

                    assert response.status_code == 201, f"Failed for {filename}"

    async def test_unsupported_audio_formats(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test unsupported file formats."""
        unsupported_formats = [
            ("test.txt", "text/plain"),
            ("test.pdf", "application/pdf"),
            ("test.jpg", "image/jpeg"),
            ("test.flac", "audio/flac"),
        ]

        for filename, content_type in unsupported_formats:
            file_data = BytesIO(b"fake file data")

            response = await client.post(
                "/dictations/",
                headers=auth_headers,
                files={"audio": (filename, file_data, content_type)},
            )

            assert response.status_code == 400, f"Should reject {filename}"
            assert "Unsupported file type" in response.json()["detail"]


class TestIntegrationWorkflow:
    """Test complete workflow integration."""

    @patch("api.services.llm_service.LLMService.transcribe_audio")
    @patch("api.services.llm_service.LLMService.format_transcript")
    @patch("api.services.llm_service.LLMService.extract_user_preferences")
    async def test_complete_dictation_workflow(
        self,
        mock_extract,
        mock_format,
        mock_transcribe,
        client: AsyncClient,
        auth_headers: dict,
        sample_audio_data: bytes,
    ):
        """Test complete workflow: upload audio -> transcribe -> edit -> extract preferences."""
        # Mock responses
        mock_transcribe.return_value = "This is a medical note about patient care."
        mock_format.return_value = (
            "**Medical Note**\n\nThis is a medical note about patient care."
        )
        mock_extract.return_value = "The user prefers bold headers in medical notes."

        # Step 1: Upload audio for dictation
        audio_file = BytesIO(sample_audio_data)
        dictation_response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("medical_note.wav", audio_file, "audio/wav")},
        )

        assert dictation_response.status_code == 201
        dictation_data = dictation_response.json()

        # Step 2: Extract preferences from edit
        preference_response = await client.post(
            "/dictations/preference_extract",
            headers=auth_headers,
            params={
                "original_text": dictation_data["formatted_text"],
                "edited_text": "**MEDICAL NOTE**\n\nThis is a medical note about patient care.",
            },
        )

        assert preference_response.status_code == 200
        preference_data = preference_response.json()
        assert (
            preference_data["rules"]
            == "The user prefers bold headers in medical notes."
        )

        # Step 3: Get all preferences
        preferences_response = await client.get(
            "/dictations/preferences", headers=auth_headers
        )

        assert preferences_response.status_code == 200
        preferences = preferences_response.json()
        assert len(preferences) == 1
        assert (
            preferences[0]["rules"] == "The user prefers bold headers in medical notes."
        )
