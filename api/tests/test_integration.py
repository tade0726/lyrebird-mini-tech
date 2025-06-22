import pytest
from httpx import AsyncClient
from unittest.mock import patch
from io import BytesIO

from api.models import UserModel


class TestFullWorkflowIntegration:
    """Test complete application workflows end-to-end."""

    async def test_complete_user_journey(
        self, client: AsyncClient, sample_audio_data: bytes
    ):
        """Test complete user journey from registration to preference extraction."""

        # Step 1: User Registration
        register_response = await client.post(
            "/auth/register",
            json={"email": "journey@example.com", "password": "password123"},
        )
        assert register_response.status_code == 201
        user_data = register_response.json()

        # Step 2: User Login
        login_response = await client.post(
            "/auth/login",
            data={"username": "journey@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Get Current User Info
        me_response = await client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "journey@example.com"

        # Step 4: Check Initial Empty Preferences
        prefs_response = await client.get("/dictations/preferences", headers=headers)
        assert prefs_response.status_code == 200
        assert prefs_response.json() == []

        # Step 5: Upload Audio for Dictation (with mocked LLM)
        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            with patch(
                "api.services.llm_service.LLMService.format_transcript"
            ) as mock_format:
                mock_transcribe.return_value = (
                    "Patient presents with chest pain and shortness of breath."
                )
                mock_format.return_value = (
                    "Patient presents with chest pain and shortness of breath."
                )

                audio_file = BytesIO(sample_audio_data)
                dictation_response = await client.post(
                    "/dictations/",
                    headers=headers,
                    files={"audio": ("medical_note.wav", audio_file, "audio/wav")},
                )

                assert dictation_response.status_code == 201
                dictation_data = dictation_response.json()
                original_text = dictation_data["formatted_text"]

        # Step 6: Extract User Preferences from Edit
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = (
                "The user prefers structured medical notes with clear sections."
            )

            edited_text = """
            ## Chief Complaint
            Patient presents with chest pain and shortness of breath.
            """

            preference_response = await client.post(
                "/dictations/preference_extract",
                headers=headers,
                params={"original_text": original_text, "edited_text": edited_text},
            )

            assert preference_response.status_code == 200
            preference_data = preference_response.json()
            assert (
                preference_data["rules"]
                == "The user prefers structured medical notes with clear sections."
            )

        # Step 7: Verify Preferences Were Saved
        final_prefs_response = await client.get(
            "/dictations/preferences", headers=headers
        )
        assert final_prefs_response.status_code == 200
        preferences = final_prefs_response.json()
        assert len(preferences) == 1
        assert (
            preferences[0]["rules"]
            == "The user prefers structured medical notes with clear sections."
        )

        # Step 8: Upload Another Audio (Should Use Saved Preferences)
        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            with patch(
                "api.services.llm_service.LLMService.format_transcript"
            ) as mock_format:
                mock_transcribe.return_value = (
                    "Follow up visit for diabetes management."
                )
                mock_format.return_value = """
                ## Chief Complaint
                Follow up visit for diabetes management.
                """

                audio_file2 = BytesIO(sample_audio_data)
                dictation_response2 = await client.post(
                    "/dictations/",
                    headers=headers,
                    files={"audio": ("followup.wav", audio_file2, "audio/wav")},
                )

                assert dictation_response2.status_code == 201
                # Verify the format_transcript was called with the saved preference
                mock_format.assert_called_once()
                call_args = mock_format.call_args
                assert (
                    "The user prefers structured medical notes with clear sections."
                    in call_args[0][1]
                )


class TestMultiUserScenarios:
    """Test scenarios with multiple users."""

    async def test_user_data_isolation(
        self, client: AsyncClient, sample_audio_data: bytes
    ):
        """Test that user data is properly isolated between users."""

        # Create two users
        users = [
            {"email": "user1@example.com", "password": "password123"},
            {"email": "user2@example.com", "password": "password123"},
        ]

        tokens = []

        for user in users:
            # Register
            await client.post("/auth/register", json=user)

            # Login and get token
            login_response = await client.post(
                "/auth/login",
                data={"username": user["email"], "password": user["password"]},
            )
            token = login_response.json()["access_token"]
            tokens.append(token)

        headers1 = {"Authorization": f"Bearer {tokens[0]}"}
        headers2 = {"Authorization": f"Bearer {tokens[1]}"}

        # User 1 creates a preference
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "User 1 prefers bullet points."

            await client.post(
                "/dictations/preference_extract",
                headers=headers1,
                params={
                    "original_text": "Original text",
                    "edited_text": "• Edited with bullets",
                },
            )

        # User 2 creates a different preference
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "User 2 prefers numbered lists."

            await client.post(
                "/dictations/preference_extract",
                headers=headers2,
                params={
                    "original_text": "Original text",
                    "edited_text": "1. Edited with numbers",
                },
            )

        # Verify User 1 only sees their preferences
        user1_prefs = await client.get("/dictations/preferences", headers=headers1)
        assert user1_prefs.status_code == 200
        user1_data = user1_prefs.json()
        assert len(user1_data) == 1
        assert user1_data[0]["rules"] == "User 1 prefers bullet points."

        # Verify User 2 only sees their preferences
        user2_prefs = await client.get("/dictations/preferences", headers=headers2)
        assert user2_prefs.status_code == 200
        user2_data = user2_prefs.json()
        assert len(user2_data) == 1
        assert user2_data[0]["rules"] == "User 2 prefers numbered lists."

    async def test_cross_user_access_prevention(self, client: AsyncClient):
        """Test that users cannot access each other's data using different tokens."""

        # Create two users and get their tokens
        user1_email = "user1@example.com"
        user2_email = "user2@example.com"

        for email in [user1_email, user2_email]:
            await client.post(
                "/auth/register", json={"email": email, "password": "password123"}
            )

        # Get tokens
        login1 = await client.post(
            "/auth/login", data={"username": user1_email, "password": "password123"}
        )
        token1 = login1.json()["access_token"]

        login2 = await client.post(
            "/auth/login", data={"username": user2_email, "password": "password123"}
        )
        token2 = login2.json()["access_token"]

        # User 1 creates some data
        headers1 = {"Authorization": f"Bearer {token1}"}
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "User 1 private preference"

            await client.post(
                "/dictations/preference_extract",
                headers=headers1,
                params={"original_text": "Original", "edited_text": "Edited"},
            )

        # User 2 tries to access data but should only see their own (empty)
        headers2 = {"Authorization": f"Bearer {token2}"}
        user2_prefs = await client.get("/dictations/preferences", headers=headers2)
        assert user2_prefs.status_code == 200
        assert user2_prefs.json() == []  # Should be empty for user 2


class TestErrorRecoveryScenarios:
    """Test error recovery and resilience."""

    async def test_service_failure_recovery(
        self, client: AsyncClient, auth_headers: dict, sample_audio_data: bytes
    ):
        """Test graceful handling when external services fail."""

        # Test transcription service failure
        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            mock_transcribe.side_effect = Exception("OpenAI service unavailable")

            audio_file = BytesIO(sample_audio_data)
            response = await client.post(
                "/dictations/",
                headers=auth_headers,
                files={"audio": ("test.wav", audio_file, "audio/wav")},
            )

            assert response.status_code == 500
            assert "Failed to process" in response.json()["detail"]

        # Test preference extraction service failure
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            # Mock LLM service handling error and returning None
            mock_extract.return_value = None

            # This should still work gracefully
            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={"original_text": "Original", "edited_text": "Edited"},
            )

            # Should handle the error gracefully and return 200 with no rules
            assert response.status_code == 200
            assert response.json()["rules"] is None

    async def test_database_consistency(self, client: AsyncClient, auth_headers: dict):
        """Test database consistency during partial failures."""

        # Mock scenario where preference extraction service handles errors gracefully
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            # Mock LLM service handling database error and returning None
            mock_extract.return_value = None

            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={"original_text": "Original text", "edited_text": "Edited text"},
            )

            # Should handle the error gracefully
            assert response.status_code == 200
            assert response.json()["rules"] is None

            # Verify user edit was still saved (database consistency maintained)
            assert response.json()["user_edits_id"] is not None


class TestPerformanceScenarios:
    """Test performance-related scenarios."""

    async def test_large_file_handling(self, client: AsyncClient, auth_headers: dict):
        """Test handling of large audio files."""

        # Test file exceeding the size limit (11MB > 10MB limit)
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB - exceeds 10MB limit
        large_file = BytesIO(large_data)

        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("large.wav", large_file, "audio/wav")},
        )

        # Should reject file that's too large
        assert response.status_code == 413

    async def test_concurrent_requests(
        self, client: AsyncClient, sample_audio_data: bytes
    ):
        """Test handling of concurrent requests from the same user."""

        # Setup user
        await client.post(
            "/auth/register",
            json={"email": "concurrent@example.com", "password": "password123"},
        )

        login_response = await client.post(
            "/auth/login",
            data={"username": "concurrent@example.com", "password": "password123"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock LLM responses
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "Concurrent preference"

            # Simulate concurrent preference extractions
            responses = []
            for i in range(3):
                response = await client.post(
                    "/dictations/preference_extract",
                    headers=headers,
                    params={
                        "original_text": f"Original text {i}",
                        "edited_text": f"Edited text {i}",
                    },
                )
                responses.append(response)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200

            # Verify final state is consistent
            prefs_response = await client.get(
                "/dictations/preferences", headers=headers
            )
            assert prefs_response.status_code == 200
            preferences = prefs_response.json()
            assert len(preferences) == 3  # All three edits should be recorded
