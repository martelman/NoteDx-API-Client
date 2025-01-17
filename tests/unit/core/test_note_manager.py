import os
import pytest
import logging
import requests
from unittest.mock import patch, mock_open, Mock, MagicMock
from io import BytesIO
from src.notedx_sdk.core.note_manager import NoteManager
from src.notedx_sdk.exceptions import (
    ValidationError,
    UploadError,
    JobNotFoundError,
    JobError,
    NotFoundError,
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    PaymentRequiredError,
    RateLimitError,
    InternalServerError,
    NetworkError,
    MissingFieldError,
    InvalidFieldError,
    ServiceUnavailableError
)

@pytest.fixture
def mock_client():
    """Create a mock client with test API key and base URL."""
    mock_client = Mock()
    mock_client._api_key = "test_api_key"
    mock_client.base_url = "https://api.notedx.com/v1"
    return mock_client

@pytest.fixture
def note_manager(mock_client):
    """Create a NoteManager instance with mock client."""
    return NoteManager(mock_client)

def test_request_retry_on_server_error(note_manager):
    """Test retry behavior on 5xx errors."""
    # Create mock responses
    error_response = Mock()
    error_response.status_code = 500
    error_response.text = "Server Error"

    success_response = Mock()
    success_response.status_code = 200
    success_response.text = '{"status": "success"}'
    success_response.json.return_value = {"status": "success"}

    # Mock requests.request to return error twice then success
    with patch('requests.request') as mock_request:
        mock_request.side_effect = [error_response, error_response, success_response]

        result = note_manager._request("GET", "test/endpoint")
        assert result == {"status": "success"}
        assert mock_request.call_count == 3

def test_request_max_retries_exceeded(note_manager):
    """Test behavior when max retries are exceeded."""
    error_response = Mock()
    error_response.status_code = 500
    error_response.text = "Server Error"

    with patch('requests.request') as mock_request:
        mock_request.return_value = error_response

        with pytest.raises(InternalServerError) as exc_info:
            note_manager._request("GET", "test/endpoint")
        assert "Server error: Server Error" in str(exc_info.value)
        assert mock_request.call_count >= 3

@pytest.mark.parametrize("error,expected_exception,error_msg", [
    (requests.ConnectionError("Connection failed"), NetworkError, "Connection error: Connection failed"),
    (requests.Timeout("Request timed out"), NetworkError, "Request timed out: Request timed out"),
    (requests.RequestException("General error"), NetworkError, "Request failed: General error")
])
def test_request_network_errors(note_manager, error, expected_exception, error_msg):
    """Test handling of various network errors."""
    with patch('requests.request', side_effect=error):
        with pytest.raises(expected_exception) as exc_info:
            note_manager._request("GET", "test/endpoint")
        assert error_msg in str(exc_info.value)

@pytest.mark.parametrize("status_code,expected_exception,response_text,expected_msg", [
    (400, BadRequestError, "Bad request", "Bad request"),
    (401, AuthenticationError, "Invalid API key", "Invalid API key: Invalid API key"),
    (402, PaymentRequiredError, "Payment required", "Payment required: Payment required"),
    (403, AuthorizationError, "Not authorized", "API key does not have required permissions: Not authorized"),
    (404, NotFoundError, "Not found", "Resource not found: Not found"),
    (429, RateLimitError, "Rate limit exceeded", "Rate limit exceeded: Rate limit exceeded")
])
def test_request_error_responses(note_manager, status_code, expected_exception, response_text, expected_msg):
    """Test handling of various error response codes."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.text = response_text
    mock_response.json.return_value = {"error": response_text}

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(expected_exception) as exc_info:
            note_manager._request("GET", "test/endpoint")
        assert expected_msg in str(exc_info.value)

def test_process_audio_success(note_manager):
    """Test successful audio processing."""
    # Mock initial request response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"job_id": "test-job", "presigned_url": "https://example.com/upload"}'
    mock_response.json.return_value = {"job_id": "test-job", "presigned_url": "https://example.com/upload"}

    # Mock upload response
    mock_upload_response = Mock()
    mock_upload_response.status_code = 200

    mock_file = mock_open(read_data=b'test audio data')
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('builtins.open', mock_file), \
         patch('requests.request', return_value=mock_response), \
         patch('requests.put', return_value=mock_upload_response):
        result = note_manager.process_audio(
            "test.wav",
            visit_type="initialEncounter",
            recording_type="dictation",
            template="primaryCare",
            lang="en"
        )
        assert result == {"job_id": "test-job", "presigned_url": "https://example.com/upload"}

def test_process_audio_upload_network_error(note_manager):
    """Test handling of network error during audio upload."""
    mock_file = mock_open(read_data=b'test audio data')
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('builtins.open', mock_file), \
         patch('requests.request', side_effect=requests.ConnectionError("Upload failed")):
        with pytest.raises(NetworkError) as exc_info:
            note_manager.process_audio(
                "test.wav",
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare",
                lang="en"
            )
        assert "Connection error: Upload failed" in str(exc_info.value)

def test_fetch_status_success(note_manager):
    """Test successful status fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "completed", "progress": 100, "job_id": "test-job"}'
    mock_response.json.return_value = {
        "status": "completed",
        "progress": 100,
        "job_id": "test-job"
    }

    with patch('requests.request', return_value=mock_response):
        result = note_manager.fetch_status("test-job")
        assert result == mock_response.json.return_value

def test_fetch_status_not_found(note_manager):
    """Test handling of non-existent job."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Job not found"

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(JobNotFoundError):
            note_manager.fetch_status("non-existent-job")

def test_fetch_note_success(note_manager):
    """Test successful note fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"note": "Test medical note content", "note_title": "Test Note", "job_id": "test-job"}'
    mock_response.json.return_value = {
        "note": "Test medical note content",
        "note_title": "Test Note",
        "job_id": "test-job"
    }

    with patch('requests.request', return_value=mock_response):
        result = note_manager.fetch_note("test-job")
        assert result == mock_response.json.return_value

def test_fetch_note_incomplete_job(note_manager):
    """Test fetching note for incomplete job."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Note generation not completed"

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(JobError):
            note_manager.fetch_note("incomplete-job")

def test_fetch_transcript_success(note_manager):
    """Test successful transcript fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"transcript": "Test transcript content", "job_id": "test-job"}'
    mock_response.json.return_value = {
        "transcript": "Test transcript content",
        "job_id": "test-job"
    }

    with patch('requests.request', return_value=mock_response):
        result = note_manager.fetch_transcript("test-job")
        assert result == mock_response.json.return_value

def test_fetch_transcript_not_ready(note_manager):
    """Test fetching transcript before it's ready."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Transcription not completed"

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(BadRequestError):
            note_manager.fetch_transcript("incomplete-job")

def test_get_system_status_success(note_manager):
    """Test successful system status fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "operational", "services": {"transcription": "up", "note_generation": "up"}, "latency": {"avg": 150}}'
    mock_response.json.return_value = {
        "status": "operational",
        "services": {"transcription": "up", "note_generation": "up"},
        "latency": {"avg": 150}
    }

    with patch('requests.request', return_value=mock_response):
        result = note_manager.get_system_status()
        assert result == mock_response.json.return_value

def test_validate_input_valid_values(note_manager):
    """Test validation with valid input values."""
    valid_input = {
        'visit_type': 'initialEncounter',
        'recording_type': 'dictation',
        'template': 'primaryCare',
        'lang': 'en',
        'documentation_style': 'soap'
    }
    # Should not raise any exceptions
    note_manager._validate_input(**valid_input)

@pytest.mark.parametrize("field,invalid_value,expected_error", [
    ('visit_type', 'invalid', "Invalid value for visit_type. Must be one of: initialEncounter, followUp"),
    ('recording_type', 'invalid', "Invalid value for recording_type. Must be one of: dictation, conversation"),
    ('template', 'invalid', "Invalid value for template. Must be one of: primaryCare, er, psychiatry, surgicalSpecialties, medicalSpecialties, nursing, radiology, pharmacy, procedures, letter, social, wfw, smartInsert"),
    ('lang', 'es', "Invalid value for lang. Must be one of: en, fr"),
    ('output_language', 'es', "Invalid value for output_language. Must be one of: en, fr")
])
def test_validate_input_invalid_values(note_manager, field, invalid_value, expected_error):
    """Test validation with invalid input values."""
    input_data = {
        'visit_type': 'initialEncounter',
        'recording_type': 'dictation',
        'template': 'primaryCare',
        'lang': 'en'
    }
    input_data[field] = invalid_value

    with pytest.raises(InvalidFieldError) as exc_info:
        note_manager._validate_input(**input_data)
    assert expected_error in str(exc_info.value)

def test_calculate_optimal_chunk_size(note_manager):
    """Test chunk size calculation for different file sizes."""
    # Test small file
    small_size = 1024 * 1024  # 1MB
    small_chunk = note_manager._calculate_optimal_chunk_size(small_size)
    assert small_chunk == 5 * 1024 * 1024  # Should use minimum chunk size
    
    # Test large file
    large_size = 400 * 1024 * 1024  # 400MB
    large_chunk = note_manager._calculate_optimal_chunk_size(large_size)
    assert large_chunk > small_chunk
    assert large_chunk <= 50 * 1024 * 1024  # Should not exceed max chunk size

def test_validate_audio_file_valid_formats(note_manager):
    """Test audio file validation with valid formats."""
    valid_formats = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.opus', '.webm']
    
    for fmt in valid_formats:
        with patch('os.path.isfile', return_value=True), \
             patch('os.path.getsize', return_value=1024), \
             patch('builtins.open', mock_open(read_data=b'test')):
            # Should not raise any exceptions
            note_manager._validate_audio_file(f"test{fmt}")

def test_validate_audio_file_missing_file(note_manager):
    """Test validation when file doesn't exist."""
    with patch('os.path.isfile', return_value=False):
        with pytest.raises(ValidationError) as exc_info:
            note_manager._validate_audio_file("missing.mp3")
        assert "Audio file not found" in str(exc_info.value)

def test_regenerate_note_success(note_manager):
    """Test successful note regeneration."""
    # Mock status check response
    status_response = Mock()
    status_response.status_code = 200
    status_response.text = '{"status": "completed", "job_id": "test-job"}'
    status_response.json.return_value = {"status": "completed", "job_id": "test-job"}

    # Mock regenerate response
    regenerate_response = Mock()
    regenerate_response.status_code = 200
    regenerate_response.text = '{"job_id": "new-job", "status": "processing"}'
    regenerate_response.json.return_value = {"job_id": "new-job", "status": "processing"}

    with patch('requests.request') as mock_request:
        mock_request.side_effect = [status_response, regenerate_response]
        result = note_manager.regenerate_note(
            "test-job",
            template="primaryCare",
            documentation_style="soap",
            output_language="en",
            custom={"context": "Test context"}
        )
        assert result == {"job_id": "new-job", "status": "processing"}

def test_regenerate_note_job_not_found(note_manager):
    """Test regeneration with non-existent job."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Job not found"

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(JobNotFoundError) as exc_info:
            note_manager.regenerate_note("non-existent-job")
        assert "Job not found" in str(exc_info.value)

def test_regenerate_note_invalid_template(note_manager):
    """Test regeneration with invalid template."""
    # Mock the fetch_status call to avoid real HTTP request
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "completed", "job_id": "test-job"}'
    mock_response.json.return_value = {"status": "completed", "job_id": "test-job"}

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(InvalidFieldError) as exc_info:
            note_manager.regenerate_note(
                "test-job",
                template="invalid-template"
            )
        assert "Invalid value for template" in str(exc_info.value)

def test_regenerate_note_invalid_documentation_style(note_manager):
    """Test regeneration with invalid documentation style."""
    # Mock the fetch_status call to return completed status
    status_response = Mock()
    status_response.status_code = 200
    status_response.text = '{"status": "completed", "job_id": "test-job"}'
    status_response.json.return_value = {"status": "completed", "job_id": "test-job"}

    # Mock the regenerate call to return a 400 error
    error_response = Mock()
    error_response.status_code = 400
    error_response.text = "Invalid documentation_style value"

    with patch('requests.request') as mock_request:
        mock_request.side_effect = [status_response, error_response]
        with pytest.raises(BadRequestError) as exc_info:
            note_manager.regenerate_note(
                "test-job",
                template="primaryCare",
                documentation_style="invalid-style"
            )
        assert "Invalid documentation_style value" in str(exc_info.value)

def test_regenerate_note_invalid_output_language(note_manager):
    """Test regeneration with invalid output language."""
    # Mock the fetch_status call to avoid real HTTP request
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "completed", "job_id": "test-job"}'
    mock_response.json.return_value = {"status": "completed", "job_id": "test-job"}

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(InvalidFieldError) as exc_info:
            note_manager.regenerate_note(
                "test-job",
                template="primaryCare",
                output_language="es"
            )
        assert "Invalid value for output_language" in str(exc_info.value)

def test_regenerate_note_with_custom_template(note_manager):
    """Test regeneration with custom template."""
    # Mock status check response
    status_response = Mock()
    status_response.status_code = 200
    status_response.text = '{"status": "completed", "job_id": "test-job"}'
    status_response.json.return_value = {"status": "completed", "job_id": "test-job"}

    # Mock regenerate response
    regenerate_response = Mock()
    regenerate_response.status_code = 200
    regenerate_response.text = '{"job_id": "new-job", "status": "processing"}'
    regenerate_response.json.return_value = {"job_id": "new-job", "status": "processing"}

    custom_data = {
        "context": "Patient history: Hypertension",
        "template": "Custom SOAP template"
    }

    with patch('requests.request') as mock_request:
        mock_request.side_effect = [status_response, regenerate_response]
        result = note_manager.regenerate_note(
            "test-job",
            template="primaryCare",
            custom=custom_data
        )
        assert result == {"job_id": "new-job", "status": "processing"}

def test_process_audio_invalid_file_type(note_manager):
    """Test handling of invalid audio file type."""
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024):
        with pytest.raises(ValidationError) as exc_info:
            note_manager.process_audio(
                "test.txt",
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare"
            )
        assert "Unsupported audio format" in str(exc_info.value)

def test_process_audio_file_too_large(note_manager):
    """Test handling of file exceeding size limit."""
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=600 * 1024 * 1024):  # 600MB
        with pytest.raises(ValidationError) as exc_info:
            note_manager.process_audio(
                "test.mp3",
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare"
            )
        assert "File size exceeds 500MB limit" in str(exc_info.value)

def test_process_audio_missing_required_fields(note_manager):
    """Test handling of missing required fields."""
    mock_file = mock_open(read_data=b'test audio data')
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('builtins.open', mock_file):
        with pytest.raises(MissingFieldError) as exc_info:
            note_manager.process_audio(
                "test.mp3",
                visit_type="initialEncounter",
                recording_type="dictation"
                # Missing required template field
            )
        assert "Missing required field: template" in str(exc_info.value)

def test_process_audio_invalid_field_values(note_manager):
    """Test handling of invalid field values."""
    mock_file = mock_open(read_data=b'test audio data')
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('builtins.open', mock_file):
        with pytest.raises(InvalidFieldError) as exc_info:
            note_manager.process_audio(
                "test.mp3",
                visit_type="invalid",
                recording_type="dictation",
                template="primaryCare"
            )
        assert "Invalid value for visit_type" in str(exc_info.value)

def test_validate_audio_file_zero_size(note_manager):
    """Test validation of zero-size audio file."""
    mock_file = mock_open()
    mock_file.return_value.read.side_effect = [b'']  # Empty file
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.getsize', return_value=0), \
         patch('builtins.open', mock_file):
        with pytest.raises(ValidationError, match="Cannot read audio file"):
            note_manager._validate_audio_file("test.mp3")

def test_validate_audio_file_directory(note_manager):
    """Test validation when path points to a directory."""
    with patch('os.path.isfile', return_value=False), \
         patch('os.path.isdir', return_value=True):
        with pytest.raises(ValidationError) as exc_info:
            note_manager._validate_audio_file("test_dir")
        assert "Audio file not found" in str(exc_info.value)

def test_regenerate_note_server_error(note_manager):
    """Test handling of server error during note regeneration."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = '{"error": "Internal server error"}'
    mock_response.json.return_value = {
        "error": "Internal server error"
    }

    with patch('requests.request') as mock_request:
        mock_request.return_value = mock_response
        with pytest.raises(InternalServerError, match="Server error"):
            note_manager.regenerate_note("test-job", template="primaryCare")

def test_fetch_status_invalid_response(note_manager):
    """Test handling of invalid JSON response during status fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'Invalid JSON'
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(BadRequestError, match="Invalid response format"):
            note_manager.fetch_status("test-job")

def test_fetch_transcript_invalid_response(note_manager):
    """Test handling of invalid JSON response during transcript fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'Invalid JSON'
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch('requests.request', return_value=mock_response):
        with pytest.raises(BadRequestError, match="Invalid response format"):
            note_manager.fetch_transcript("test-job")

def test_process_audio_job_error(note_manager):
    """Test handling of job error after successful upload."""
    mock_file = mock_open(read_data=b'test audio data')

    # Mock job error response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = '{"error": "Job processing failed", "job_id": "test-job"}'
    mock_response.json.return_value = {
        "error": "Job processing failed",
        "job_id": "test-job"
    }

    with patch('os.path.isfile', return_value=True), \
         patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('builtins.open', mock_file), \
         patch('requests.request') as mock_request:
        mock_request.return_value = mock_response
        with pytest.raises(BadRequestError, match="Job processing failed"):
            note_manager.process_audio(
                "test.mp3",
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare"
            )

def test_process_audio_service_unavailable(note_manager):
    """Test handling of service unavailable error."""
    mock_file = mock_open(read_data=b'test audio data')
    
    mock_response = Mock()
    mock_response.status_code = 503
    mock_response.text = '{"error": "Service temporarily unavailable"}'
    mock_response.json.return_value = {
        "error": "Service temporarily unavailable"
    }

    with patch('os.path.isfile', return_value=True), \
         patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('builtins.open', mock_file), \
         patch('requests.request') as mock_request:
        mock_request.return_value = mock_response
        with pytest.raises(InternalServerError) as exc_info:
            note_manager.process_audio(
                "test.mp3",
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare"
            )
        assert "Service temporarily unavailable" in str(exc_info.value)
