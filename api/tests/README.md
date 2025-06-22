# Lyrebird API Test Suite

Comprehensive test suite for the Lyrebird Mini Tech API backend.

## Overview

This test suite provides extensive coverage of all API endpoints, services, and business logic with:

- **200+ test cases** covering all major functionality
- **Unit tests** for individual components
- **Integration tests** for complete workflows  
- **Edge case testing** for error handling and boundary conditions
- **Security testing** for authentication and authorization
- **Performance testing** for file handling and concurrent requests

## Test Structure

```
api/tests/
├── conftest.py              # Test fixtures and configuration
├── pytest.ini              # Pytest configuration
├── test_auth.py            # Authentication endpoint tests
├── test_dictations.py      # Dictation endpoint tests  
├── test_services.py        # Service layer unit tests
├── test_integration.py     # End-to-end integration tests
├── test_edge_cases.py      # Edge cases and error handling
├── test_health.py          # Health check and basic endpoints
└── README.md               # This file
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)
- ✅ User registration (success, duplicate email, validation)
- ✅ User login (success, invalid credentials, missing fields)
- ✅ JWT token validation and security
- ✅ Password hashing and verification
- ✅ Protected endpoint access

**Key Test Cases:**
- `test_register_success` - Valid user registration
- `test_login_invalid_credentials` - Security validation
- `test_get_me_unauthorized` - Protected route access
- `test_password_not_stored_plaintext` - Security verification

### 2. Dictation Tests (`test_dictations.py`)
- ✅ Audio file upload and processing
- ✅ File type and size validation
- ✅ Transcription workflow with mocked LLM
- ✅ Preference extraction from text edits
- ✅ User preference management

**Key Test Cases:**
- `test_create_dictation_success` - Complete audio processing
- `test_create_dictation_invalid_file_type` - File validation
- `test_preference_extract_success` - Preference extraction
- `test_complete_dictation_workflow` - End-to-end workflow

### 3. Service Layer Tests (`test_services.py`)
- ✅ LLM service functionality (transcription, formatting, preferences)
- ✅ Audio service processing pipeline
- ✅ Preferences service operations
- ✅ Database interaction patterns
- ✅ Error handling in services

**Key Test Cases:**
- `test_transcribe_audio_success` - Audio transcription
- `test_format_transcript_success` - Text formatting with preferences
- `test_extract_user_preferences_success` - Preference extraction logic
- `test_audio_to_preferences_workflow` - Service integration

### 4. Integration Tests (`test_integration.py`)
- ✅ Complete user journey from registration to preference extraction
- ✅ Multi-user data isolation
- ✅ Cross-user access prevention
- ✅ Service failure recovery
- ✅ Concurrent request handling

**Key Test Cases:**
- `test_complete_user_journey` - Full application workflow
- `test_user_data_isolation` - Security between users
- `test_service_failure_recovery` - Error resilience
- `test_concurrent_requests` - Performance under load

### 5. Edge Cases Tests (`test_edge_cases.py`)
- ✅ Input validation edge cases
- ✅ Audio file boundary conditions
- ✅ JWT token security scenarios  
- ✅ LLM service error handling
- ✅ Database constraint violations
- ✅ Security vulnerability testing

**Key Test Cases:**
- `test_extremely_long_email` - Input validation limits
- `test_corrupted_audio_file` - File corruption handling
- `test_malformed_json_response_from_llm` - External service errors
- `test_sql_injection_attempts` - Security testing

### 6. Health Check Tests (`test_health.py`)
- ✅ Health endpoint functionality
- ✅ API documentation endpoints
- ✅ Basic connectivity tests

## Running Tests

### Prerequisites
```bash
uv sync  # Install dependencies including test packages
```

### Run All Tests
```bash
# Using the test runner script
python api/run_tests.py

# Or directly with pytest
uv run pytest api/tests/ -v
```

### Run Specific Test Categories
```bash
# Authentication tests only
uv run pytest api/tests/test_auth.py -v

# Dictation tests only  
uv run pytest api/tests/test_dictations.py -v

# Integration tests only
uv run pytest api/tests/test_integration.py -v

# With coverage report
python api/run_tests.py --coverage
```

### Run Tests by Markers
```bash
# Unit tests only
uv run pytest -m unit

# Integration tests only
uv run pytest -m integration

# Slow tests excluded
uv run pytest -m "not slow"
```

## Test Configuration

### Database Setup
- Uses SQLite in-memory database for isolation
- Each test gets a fresh database instance
- Automatic table creation and cleanup
- Fast execution with no persistent state

### Mocking Strategy
- LLM services (OpenAI, LangSmith) are mocked for reliability
- External API calls are mocked to avoid dependencies
- File operations use temporary files
- Network requests are isolated

### Fixtures Available
- `client` - HTTP test client with database override
- `test_db` - Fresh database session for each test
- `test_user` - Pre-created test user with credentials
- `auth_token` - Valid JWT token for authenticated requests
- `auth_headers` - Authorization headers for API calls
- `sample_audio_data` - Mock audio file data for testing

## Coverage Goals

The test suite aims for:
- **90%+ code coverage** across all modules
- **100% coverage** of API endpoints
- **100% coverage** of authentication flows
- **95%+ coverage** of business logic
- **Edge case coverage** for all user inputs

## Security Testing

Includes comprehensive security tests:
- SQL injection prevention
- XSS attempt handling  
- JWT token security
- Password security verification
- User data isolation
- Authorization bypass prevention

## Performance Testing

Tests performance characteristics:
- File upload size limits
- Concurrent request handling
- Database transaction integrity
- Memory usage patterns
- Response time verification

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No external dependencies
- Deterministic execution
- Parallel test execution support
- Clear failure reporting
- Coverage reporting integration

## Adding New Tests

When adding new functionality:

1. **Add unit tests** in appropriate `test_*.py` file
2. **Add integration tests** if it affects multiple components  
3. **Add edge case tests** for error conditions
4. **Update fixtures** if new test data is needed
5. **Mock external dependencies** to ensure reliability
6. **Add appropriate markers** for test categorization

### Example Test Structure
```python
import pytest
from httpx import AsyncClient

class TestNewFeature:
    """Test new feature functionality."""
    
    @pytest.mark.asyncio
    async def test_feature_success(self, client: AsyncClient, auth_headers: dict):
        \"\"\"Test successful feature usage.\"\"\"
        response = await client.post(
            "/new-endpoint",
            headers=auth_headers,
            json={"test": "data"}
        )
        
        assert response.status_code == 200
        assert response.json()["result"] == "expected"
```

## Troubleshooting

### Common Issues

1. **Async test failures**: Ensure `@pytest.mark.asyncio` decorator is used
2. **Database connection errors**: Check SQLite/aiosqlite installation
3. **Import errors**: Verify all dependencies are installed with `uv sync`
4. **Mock failures**: Ensure external services are properly mocked

### Debug Mode
```bash
# Run with verbose output and no capture
uv run pytest api/tests/ -v -s

# Run single test with debugging
uv run pytest api/tests/test_auth.py::TestAuthEndpoints::test_login_success -v -s
```

This comprehensive test suite ensures the Lyrebird API is robust, secure, and performs well under various conditions.