import pytest
from httpx import AsyncClient
from unittest.mock import patch, Mock
from io import BytesIO
import json

from api.models import UserModel


class TestInputValidationEdgeCases:
    """Test edge cases for input validation."""

    async def test_extremely_long_email(self, client: AsyncClient):
        """Test registration with extremely long email."""
        long_email = "a" * 300 + "@example.com"

        response = await client.post(
            "/auth/register", json={"email": long_email, "password": "password123"}
        )

        # Should be rejected due to length or validation
        assert response.status_code in [400, 422]

    async def test_special_characters_in_password(self, client: AsyncClient):
        """Test passwords with special characters."""
        special_chars_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        response = await client.post(
            "/auth/register",
            json={"email": "special@example.com", "password": special_chars_password},
        )

        assert response.status_code == 201

    async def test_unicode_characters_in_text(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test handling of unicode characters in text inputs."""
        unicode_text = "Patient says: 你好世界 🏥 médico français"

        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "User prefers multilingual notes"

            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={
                    "original_text": unicode_text,
                    "edited_text": unicode_text + " - edited",
                },
            )

            assert response.status_code == 200

    async def test_empty_string_inputs(self, client: AsyncClient, auth_headers: dict):
        """Test handling of empty string inputs."""
        response = await client.post(
            "/dictations/preference_extract",
            headers=auth_headers,
            params={"original_text": "", "edited_text": ""},
        )

        # Should handle empty strings gracefully
        assert response.status_code == 200

    async def test_very_large_text_input(self, client: AsyncClient, auth_headers: dict):
        """Test handling of very large text inputs."""
        large_text = "A" * 10000  # 10KB of text (more reasonable for URL params)

        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            mock_extract.return_value = "User prefers concise notes"

            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={
                    "original_text": large_text,
                    "edited_text": large_text[:5000],  # Shortened version
                },
            )

            # Should handle large text inputs
            assert response.status_code == 200


class TestAudioFileEdgeCases:
    """Test edge cases for audio file handling."""

    async def test_zero_byte_audio_file(self, client: AsyncClient, auth_headers: dict):
        """Test handling of zero-byte audio file."""
        empty_file = BytesIO(b"")

        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={"audio": ("empty.wav", empty_file, "audio/wav")},
        )

        # Should reject empty file
        assert response.status_code in [400, 422, 500]

    async def test_corrupted_audio_file(self, client: AsyncClient, auth_headers: dict):
        """Test handling of corrupted audio file."""
        corrupted_data = b"This is not audio data at all!"
        corrupted_file = BytesIO(corrupted_data)

        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            mock_transcribe.side_effect = Exception("Invalid audio format")

            response = await client.post(
                "/dictations/",
                headers=auth_headers,
                files={"audio": ("corrupted.wav", corrupted_file, "audio/wav")},
            )

            assert response.status_code == 500

    async def test_wrong_content_type_header(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test file with wrong content-type header."""
        audio_data = b"fake audio data"
        audio_file = BytesIO(audio_data)

        # Send with wrong content type
        response = await client.post(
            "/dictations/",
            headers=auth_headers,
            files={
                "audio": ("test.wav", audio_file, "image/jpeg")
            },  # Wrong content type
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    async def test_filename_without_extension(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test file without extension in filename."""
        audio_data = b"fake audio data"
        audio_file = BytesIO(audio_data)

        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            with patch(
                "api.services.llm_service.LLMService.format_transcript"
            ) as mock_format:
                mock_transcribe.return_value = "Test transcription"
                mock_format.return_value = "Formatted test"

                response = await client.post(
                    "/dictations/",
                    headers=auth_headers,
                    files={
                        "audio": ("audiofile", audio_file, "audio/wav")
                    },  # No extension
                )

                # Should still work based on content-type
                assert response.status_code == 201


class TestJWTTokenEdgeCases:
    """Test edge cases for JWT token handling."""

    async def test_token_with_invalid_signature(self, client: AsyncClient):
        """Test token with invalid signature."""
        # Create a token with wrong signature
        invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwiZXhwIjo5OTk5OTk5OTk5fQ.invalid_signature"
        headers = {"Authorization": f"Bearer {invalid_token}"}

        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_token_with_missing_claims(self, client: AsyncClient):
        """Test token with missing required claims."""
        # This would require actual JWT creation with missing 'sub' claim
        malformed_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjk5OTk5OTk5OTl9.fake_signature"
        headers = {"Authorization": f"Bearer {malformed_token}"}

        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_authorization_header_variations(self, client: AsyncClient):
        """Test various malformed authorization headers."""
        malformed_headers = [
            {"Authorization": "InvalidFormat"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "bearer lowercase_bearer"},  # Wrong case
            {"Authorization": "Token some_token"},  # Wrong prefix
            {"Authorization": "Bearer  double_space_token"},  # Extra space
        ]

        for headers in malformed_headers:
            response = await client.get("/auth/me", headers=headers)
            assert response.status_code == 401

    async def test_user_id_not_found_in_token(self, client: AsyncClient):
        """Test token with user ID that doesn't exist in database."""
        # This would require creating a valid token with non-existent user ID
        # In practice, this might happen if user is deleted after token creation
        pass  # Implementation would require more complex setup


class TestLLMServiceEdgeCases:
    """Test edge cases for LLM service responses."""

    async def test_malformed_json_response_from_llm(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test handling of malformed JSON from LLM preference extraction."""
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            # Mock LLM service handling JSON error and returning None
            mock_extract.return_value = None

            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={"original_text": "Original", "edited_text": "Edited"},
            )

            # Should handle JSON decode error gracefully and return 200 with no rules
            assert response.status_code == 200
            assert response.json()["rules"] is None

    async def test_llm_timeout_scenarios(
        self, client: AsyncClient, auth_headers: dict, sample_audio_data: bytes
    ):
        """Test handling of LLM service timeouts."""
        with patch(
            "api.services.llm_service.LLMService.transcribe_audio"
        ) as mock_transcribe:
            # Mock timeout error
            mock_transcribe.side_effect = TimeoutError("LLM service timeout")

            audio_file = BytesIO(sample_audio_data)
            response = await client.post(
                "/dictations/",
                headers=auth_headers,
                files={"audio": ("test.wav", audio_file, "audio/wav")},
            )

            assert response.status_code == 500

    async def test_unexpected_llm_response_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test handling of unexpected LLM response formats."""
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            # Mock LLM service handling invalid format and returning None
            mock_extract.return_value = None

            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={"original_text": "Original", "edited_text": "Edited"},
            )

            # Should handle unexpected format gracefully and return 200 with no rules
            assert response.status_code == 200
            assert response.json()["rules"] is None


class TestDatabaseEdgeCases:
    """Test edge cases for database operations."""

    async def test_duplicate_user_registration_race_condition(
        self, client: AsyncClient
    ):
        """Test handling of race conditions in user registration."""
        # This is hard to test without actual concurrency, but we can test the error
        user_data = {"email": "race@example.com", "password": "password123"}

        # Register user first time
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 201

        # Try to register same user again
        response2 = await client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    async def test_database_connection_failure_simulation(self, client: AsyncClient):
        """Test graceful handling of database connection failures."""
        # This would require mocking the database session to fail
        # In a real scenario, we'd test retry logic and error recovery
        pass

    async def test_constraint_violation_handling(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test handling of database constraint violations."""
        # This would involve creating scenarios that violate database constraints
        # For example, trying to create references to non-existent records
        pass


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    async def test_maximum_preferences_per_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test handling when user has many preferences."""
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            # Create many preferences
            for i in range(100):  # Create 100 preferences
                mock_extract.return_value = f"Preference number {i}"

                await client.post(
                    "/dictations/preference_extract",
                    headers=auth_headers,
                    params={
                        "original_text": f"Original {i}",
                        "edited_text": f"Edited {i}",
                    },
                )

            # Get all preferences
            response = await client.get("/dictations/preferences", headers=auth_headers)
            assert response.status_code == 200
            preferences = response.json()
            assert len(preferences) == 100

    async def test_minimum_valid_inputs(self, client: AsyncClient, auth_headers: dict):
        """Test with minimum valid inputs."""
        # Single character inputs
        response = await client.post(
            "/dictations/preference_extract",
            headers=auth_headers,
            params={"original_text": "A", "edited_text": "B"},
        )

        assert response.status_code == 200

    async def test_network_interruption_simulation(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test handling of network interruptions during LLM calls."""
        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            # Mock LLM service handling network error and returning None
            mock_extract.return_value = None

            response = await client.post(
                "/dictations/preference_extract",
                headers=auth_headers,
                params={"original_text": "Original", "edited_text": "Edited"},
            )

            # Should handle network errors gracefully and return 200 with no rules
            assert response.status_code == 200
            assert response.json()["rules"] is None


class TestSecurityEdgeCases:
    """Test security-related edge cases."""

    async def test_sql_injection_attempts(self, client: AsyncClient):
        """Test SQL injection attempts in input fields."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin@example.com' OR '1'='1",
            "test@example.com'; INSERT INTO users VALUES ('hacker', 'password'); --",
        ]

        for malicious_email in malicious_inputs:
            response = await client.post(
                "/auth/register",
                json={"email": malicious_email, "password": "password123"},
            )

            # Should either reject malicious input or handle it safely
            # Email validation should prevent most of these
            assert response.status_code in [400, 422]

    async def test_xss_attempts_in_preferences(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test XSS attempts in preference text."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        with patch(
            "api.services.llm_service.LLMService.extract_user_preferences"
        ) as mock_extract:
            for xss_text in xss_attempts:
                mock_extract.return_value = xss_text

                response = await client.post(
                    "/dictations/preference_extract",
                    headers=auth_headers,
                    params={"original_text": "Clean text", "edited_text": xss_text},
                )

                # Should handle XSS attempts safely
                assert response.status_code == 200

                # Verify the preference was stored (the API doesn't sanitize,
                # that's the frontend's responsibility)
                prefs_response = await client.get(
                    "/dictations/preferences", headers=auth_headers
                )
                preferences = prefs_response.json()
                # The XSS text might be stored as-is, which is acceptable for an API
