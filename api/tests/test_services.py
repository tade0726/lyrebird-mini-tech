import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.llm_service import LLMService
from api.services.audio_service import AudioService, PreferencesService
from api.models import UserModel, DictationsModel, UserPreferencesModel, UserEditsModel
from api.schemas import UserEditsInput


class TestLLMService:
    """Test LLM service functionality."""

    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance."""
        with patch("api.services.llm_service.LangSmithClient"):
            with patch("api.services.llm_service.wrap_openai"):
                return LLMService()

    @patch("api.services.llm_service.tempfile.NamedTemporaryFile")
    @patch("builtins.open")
    async def test_transcribe_audio_success(
        self, mock_open, mock_tempfile, llm_service
    ):
        """Test successful audio transcription."""
        # Mock tempfile with context manager support
        mock_file = Mock()
        mock_file.name = "/tmp/test.mpga"
        mock_file.write = Mock()
        mock_tempfile.return_value.__enter__ = Mock(return_value=mock_file)
        mock_tempfile.return_value.__exit__ = Mock(return_value=None)

        # Mock file open for reading
        mock_audio_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        # Mock OpenAI response
        mock_transcription = Mock()
        mock_transcription.text = "This is a test transcription."
        llm_service.openai_client.audio.transcriptions.create = AsyncMock(
            return_value=mock_transcription
        )

        result = await llm_service.transcribe_audio(b"fake audio data")

        assert result == "This is a test transcription."

    async def test_transcribe_audio_failure(self, llm_service):
        """Test audio transcription failure."""
        # Mock OpenAI failure
        llm_service.openai_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("OpenAI API error")
        )

        with pytest.raises(Exception):
            await llm_service.transcribe_audio(b"fake audio data")

    async def test_format_transcript_success(self, llm_service):
        """Test successful transcript formatting."""
        # Mock LangSmith prompt
        mock_prompt = Mock()
        mock_prompt.format.return_value = "Format this transcript"
        llm_service.langsmith_client.pull_prompt.return_value = mock_prompt

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "**Formatted transcript**"
        llm_service.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.format_transcript(
            "Raw transcript", ["User prefers bold headers"]
        )

        assert result == "**Formatted transcript**"

    async def test_extract_user_preferences_success(self, llm_service):
        """Test successful preference extraction."""
        # Mock LangSmith prompt
        mock_prompt = Mock()
        mock_prompt.format.return_value = "Extract preferences"
        llm_service.langsmith_client.pull_prompt.return_value = mock_prompt

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            '{"memory_to_write": "User prefers bullet points"}'
        )
        llm_service.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.extract_user_preferences(
            "Original text", "Edited text with bullets", ["Existing preference"]
        )

        assert result == "User prefers bullet points"

    async def test_extract_user_preferences_no_memory(self, llm_service):
        """Test preference extraction when no memory should be written."""
        # Mock prompt
        mock_prompt = Mock()
        mock_prompt.format.return_value = "Extract preferences"
        llm_service.langsmith_client.pull_prompt.return_value = mock_prompt

        # Mock OpenAI response with no memory
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"memory_to_write": false}'
        llm_service.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.extract_user_preferences("Original", "Same text", [])

        assert result is None


class TestAudioService:
    """Test audio service functionality."""

    @pytest.fixture
    def audio_service(self, test_db):
        """Create audio service instance."""
        return AudioService(test_db)

    @patch("api.services.audio_service.LLMService")
    async def test_process_audio_success(
        self, mock_llm_class, audio_service, test_user
    ):
        """Test successful audio processing."""
        # Mock LLM service
        mock_llm = Mock()
        mock_llm.transcribe_audio = AsyncMock(return_value="Test transcription")
        mock_llm.format_transcript = AsyncMock(return_value="**Test formatted**")
        mock_llm_class.return_value = mock_llm

        # Create new service instance with mocked LLM
        audio_service.llm_service = mock_llm

        result = await audio_service.process_audio(b"fake audio", test_user.id)

        assert result.text == "Test transcription"
        assert result.formatted_text == "**Test formatted**"
        assert result.user_id == test_user.id

    @patch("api.services.audio_service.LLMService")
    async def test_process_audio_with_preferences(
        self, mock_llm_class, audio_service, test_user, test_db
    ):
        """Test audio processing with existing preferences."""
        # Add a preference for the user
        preference = UserPreferencesModel(
            user_id=test_user.id, user_edits_id=1, rules="User prefers bullet points"
        )
        test_db.add(preference)
        await test_db.commit()

        # Mock LLM service
        mock_llm = Mock()
        mock_llm.transcribe_audio = AsyncMock(return_value="Test transcription")
        mock_llm.format_transcript = AsyncMock(return_value="• Formatted with bullets")
        mock_llm_class.return_value = mock_llm

        audio_service.llm_service = mock_llm

        result = await audio_service.process_audio(b"fake audio", test_user.id)

        # Verify format_transcript was called with preferences
        mock_llm.format_transcript.assert_called_once_with(
            "Test transcription", ["User prefers bullet points"]
        )

    @patch("api.services.audio_service.LLMService")
    async def test_process_audio_transcription_failure(
        self, mock_llm_class, audio_service, test_user
    ):
        """Test audio processing when transcription fails."""
        # Mock LLM service failure
        mock_llm = Mock()
        mock_llm.transcribe_audio = AsyncMock(
            side_effect=Exception("Transcription failed")
        )
        mock_llm_class.return_value = mock_llm

        audio_service.llm_service = mock_llm

        with pytest.raises(Exception):
            await audio_service.process_audio(b"fake audio", test_user.id)


class TestPreferencesService:
    """Test preferences service functionality."""

    @pytest.fixture
    def preferences_service(self, test_db):
        """Create preferences service instance."""
        return PreferencesService(test_db)

    @patch("api.services.audio_service.LLMService")
    async def test_extract_preferences_success(
        self, mock_llm_class, preferences_service, test_user
    ):
        """Test successful preference extraction."""
        # Mock LLM service
        mock_llm = Mock()
        mock_llm.extract_user_preferences = AsyncMock(
            return_value="User prefers numbered lists"
        )
        mock_llm_class.return_value = mock_llm

        preferences_service.llm_service = mock_llm

        user_edits = UserEditsInput(
            user_id=test_user.id,
            original_text="Original text",
            edited_text="1. Edited text with numbers",
        )

        result = await preferences_service.extract_preferences(user_edits)

        assert result.rules == "User prefers numbered lists"
        assert result.user_id == test_user.id
        assert result.id is not None

    @patch("api.services.audio_service.LLMService")
    async def test_extract_preferences_no_new_preference(
        self, mock_llm_class, preferences_service, test_user
    ):
        """Test preference extraction when no new preference is found."""
        # Mock LLM service returning None
        mock_llm = Mock()
        mock_llm.extract_user_preferences = AsyncMock(return_value=None)
        mock_llm_class.return_value = mock_llm

        preferences_service.llm_service = mock_llm

        user_edits = UserEditsInput(
            user_id=test_user.id, original_text="Same text", edited_text="Same text"
        )

        result = await preferences_service.extract_preferences(user_edits)

        assert result.rules is None
        assert result.id is None
        assert result.user_edits_id is not None  # User edit should still be saved

    async def test_get_user_preferences_empty(self, preferences_service, test_user):
        """Test getting preferences when none exist."""
        result = await preferences_service.get_user_preferences(test_user.id)

        assert result == []

    async def test_get_user_preferences_with_data(
        self, preferences_service, test_user, test_db
    ):
        """Test getting preferences with existing data."""
        # Add preferences
        preference1 = UserPreferencesModel(
            user_id=test_user.id, user_edits_id=1, rules="First preference"
        )
        preference2 = UserPreferencesModel(
            user_id=test_user.id, user_edits_id=2, rules="Second preference"
        )

        test_db.add(preference1)
        test_db.add(preference2)
        await test_db.commit()

        result = await preferences_service.get_user_preferences(test_user.id)

        assert len(result) == 2
        rules = [pref.rules for pref in result]
        assert "First preference" in rules
        assert "Second preference" in rules


class TestServiceIntegration:
    """Test service integration scenarios."""

    @patch("api.services.llm_service.LangSmithClient")
    @patch("api.services.llm_service.wrap_openai")
    async def test_audio_to_preferences_workflow(
        self, mock_wrap_openai, mock_langsmith, test_db, test_user
    ):
        """Test complete workflow from audio to preferences."""
        # Setup services
        audio_service = AudioService(test_db)
        preferences_service = PreferencesService(test_db)

        # Mock all LLM operations
        with patch.object(
            audio_service.llm_service, "transcribe_audio"
        ) as mock_transcribe:
            with patch.object(
                audio_service.llm_service, "format_transcript"
            ) as mock_format:
                with patch.object(
                    preferences_service.llm_service, "extract_user_preferences"
                ) as mock_extract:

                    # Setup mocks
                    mock_transcribe.return_value = "Patient has symptoms"
                    mock_format.return_value = "**Patient has symptoms**"
                    mock_extract.return_value = "User prefers bold headers"

                    # Step 1: Process audio
                    dictation = await audio_service.process_audio(
                        b"fake audio", test_user.id
                    )

                    # Step 2: Extract preferences from edit
                    user_edits = UserEditsInput(
                        user_id=test_user.id,
                        original_text=dictation.formatted_text,
                        edited_text="**PATIENT HAS SYMPTOMS**",
                    )

                    preference = await preferences_service.extract_preferences(
                        user_edits
                    )

                    # Step 3: Verify workflow
                    assert dictation.text == "Patient has symptoms"
                    assert preference.rules == "User prefers bold headers"

                    # Step 4: Get all preferences
                    all_preferences = await preferences_service.get_user_preferences(
                        test_user.id
                    )
                    assert len(all_preferences) == 1
                    assert all_preferences[0].rules == "User prefers bold headers"
