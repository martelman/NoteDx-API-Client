import os
import pytest
import requests
from unittest.mock import patch, mock_open
from src.notedx_sdk.exceptions import (
    ValidationError,
    UploadError,
    JobNotFoundError,
    JobError,
    NotFoundError,
    BadRequestError
)

# Test Data
VALID_AUDIO_FILE = "test.mp3"
INVALID_AUDIO_FILE = "test.xyz"
LARGE_FILE_SIZE = 600 * 1024 * 1024  # 600MB

@pytest.fixture
def note_manager(mock_client):
    """Create a NoteManager instance with a mock client."""
    manager = mock_client.notes
    # Initialize with default configuration
    manager._config = {
        'api_base_url': "https://api.notedx.io/v1",
        'request_timeout': 60,
        'max_retries': 3,
        'retry_delay': 1,
        'retry_max_delay': 30,
        'retry_on_status': [408, 429, 500, 502, 503, 504]
    }
    
    # Mock the _request method to avoid real HTTP calls
    manager._request = mock_client._request
    return manager

@pytest.fixture
def mock_file_exists():
    """Mock os.path.isfile to return True for test files."""
    with patch('os.path.isfile') as mock:
        mock.return_value = True
        yield mock

@pytest.fixture
def mock_file_size():
    """Mock os.path.getsize to return a valid file size."""
    with patch('os.path.getsize') as mock:
        mock.return_value = 1024 * 1024  # 1MB
        yield mock

class TestNoteManagerInit:
    """Test NoteManager initialization and configuration."""
    
    def test_init_creates_logger(self, note_manager):
        """Test that logger is properly initialized."""
        assert note_manager.logger is not None
        # The logger name should include the module path
        expected_name = "notedx_sdk.core.note_manager.NoteManager"
        assert note_manager.logger.name.endswith(expected_name)

class TestNoteManagerProcessAudio:
    """Test process_audio method functionality."""

    def test_process_audio_success(self, note_manager, mock_file_exists, mock_file_size):
        """Test successful audio processing."""
        # Mock successful API response
        note_manager._client._request.return_value = {
            "job_id": "test-job",
            "presigned_url": "https://test-url.com",
            "status": "pending"
        }
        
        # Mock successful file upload
        with patch('builtins.open', mock_open(read_data=b'test data')):
            with patch('requests.put') as mock_put:
                mock_put.return_value.status_code = 200
                
                result = note_manager.process_audio(
                    file_path=VALID_AUDIO_FILE,
                    visit_type="initialEncounter",
                    recording_type="dictation",
                    template="primaryCare",
                    lang="en"
                )
        
        assert result["job_id"] == "test-job"
        assert result["status"] == "pending"
        assert "presigned_url" in result

    def test_process_audio_invalid_file_format(self, note_manager, mock_file_exists):
        """Test handling of invalid audio file format."""
        with pytest.raises(ValidationError) as exc_info:
            note_manager.process_audio(
                file_path=INVALID_AUDIO_FILE,
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare"
            )
        assert "Unsupported audio format" in str(exc_info.value)

    def test_process_audio_file_too_large(self, note_manager, mock_file_exists):
        """Test handling of files exceeding size limit."""
        with patch('os.path.getsize', return_value=LARGE_FILE_SIZE):
            with pytest.raises(ValidationError) as exc_info:
                note_manager.process_audio(
                    file_path=VALID_AUDIO_FILE,
                    visit_type="initialEncounter",
                    recording_type="dictation",
                    template="primaryCare"
                )
            assert "File size exceeds 500MB limit" in str(exc_info.value)

    def test_process_audio_missing_required_fields(self, note_manager, mock_file_exists, mock_file_size):
        """Test validation of required fields."""
        with pytest.raises(ValidationError):
            note_manager.process_audio(
                file_path=VALID_AUDIO_FILE,
                # Missing required fields
            )

    def test_process_audio_upload_network_error(self, note_manager, mock_file_exists, mock_file_size):
        """Test handling of network errors during upload."""
        note_manager._client._request.return_value = {
            "job_id": "test-job",
            "presigned_url": "https://test-url.com"
        }
        
        with patch('builtins.open', mock_open(read_data=b'test data')):
            with patch('requests.put', side_effect=requests.ConnectionError("Connection failed")):
                with pytest.raises(UploadError) as exc_info:
                    note_manager.process_audio(
                        file_path=VALID_AUDIO_FILE,
                        visit_type="initialEncounter",
                        recording_type="dictation",
                        template="primaryCare"
                    )
                assert "Connection failed" in str(exc_info.value)

class TestNoteManagerRegenerateNote:
    """Test regenerate_note method functionality."""

    def test_regenerate_note_success(self, note_manager):
        """Test successful note regeneration."""
        # Mock successful status check
        with patch.object(note_manager, 'fetch_status') as mock_status:
            mock_status.return_value = {"status": "completed"}
            
            # Mock regenerate API call
            note_manager._client._request.return_value = {
                "job_id": "new-job",
                "status": "pending"
            }
            
            result = note_manager.regenerate_note(
                job_id="test-job",
                template="er",
                output_language="fr"
            )
            
            assert result["job_id"] == "new-job"
            assert result["status"] == "pending"

    def test_regenerate_note_invalid_job(self, note_manager):
        """Test regeneration with invalid job ID."""
        with patch.object(note_manager, 'fetch_status', side_effect=JobNotFoundError("test-job")):
            with pytest.raises(JobNotFoundError):
                note_manager.regenerate_note(job_id="test-job")

    def test_regenerate_note_incomplete_job(self, note_manager):
        """Test regeneration with incomplete original job."""
        with patch.object(note_manager, 'fetch_status') as mock_status:
            mock_status.return_value = {"status": "processing"}
            
            with pytest.raises(JobError) as exc_info:
                note_manager.regenerate_note(job_id="test-job")
            assert "Cannot regenerate note" in str(exc_info.value)

class TestNoteManagerFetchStatus:
    """Test fetch_status method functionality."""

    def test_fetch_status_success(self, note_manager):
        """Test successful status fetch."""
        expected_response = {
            "status": "completed",
            "message": "Note generation complete",
            "progress": {"percent": 100}
        }
        note_manager._client._request.return_value = expected_response
        
        result = note_manager.fetch_status("test-job")
        assert result == expected_response

    def test_fetch_status_not_found(self, note_manager):
        """Test handling of non-existent job."""
        note_manager._client._request.side_effect = NotFoundError("Job not found")
        
        with pytest.raises(JobNotFoundError):
            note_manager.fetch_status("non-existent-job")

class TestNoteManagerFetchNote:
    """Test fetch_note method functionality."""

    def test_fetch_note_success(self, note_manager):
        """Test successful note fetch."""
        expected_response = {
            "note": "Test medical note content",
            "noteTitle": "Test Note",
            "job_id": "test-job"
        }
        note_manager._client._request.return_value = expected_response
        
        result = note_manager.fetch_note("test-job")
        assert result == expected_response

    def test_fetch_note_incomplete_job(self, note_manager):
        """Test fetching note for incomplete job."""
        note_manager._client._request.side_effect = BadRequestError("Note generation not completed")
        
        with pytest.raises(JobError) as exc_info:
            note_manager.fetch_note("incomplete-job")
        assert "Note generation not completed" in str(exc_info.value)

class TestNoteManagerFetchTranscript:
    """Test fetch_transcript method functionality."""

    def test_fetch_transcript_success(self, note_manager):
        """Test successful transcript fetch."""
        expected_response = {
            "transcript": "Test transcript content",
            "job_id": "test-job"
        }
        note_manager._client._request.return_value = expected_response
        
        result = note_manager.fetch_transcript("test-job")
        assert result == expected_response

    def test_fetch_transcript_not_ready(self, note_manager):
        """Test fetching transcript before it's ready."""
        note_manager._client._request.side_effect = BadRequestError("Transcription not completed")
    
        with pytest.raises(BadRequestError) as exc_info:
            note_manager.fetch_transcript("incomplete-job")
        
        assert str(exc_info.value) == "Transcription not completed"

class TestNoteManagerSystemStatus:
    """Test get_system_status method functionality."""

    def test_get_system_status_success(self, note_manager):
        """Test successful system status fetch."""
        expected_response = {
            "status": "operational",
            "services": {"transcription": "up", "note_generation": "up"},
            "latency": {"avg": 150}
        }
        note_manager._client._request.return_value = expected_response
        
        result = note_manager.get_system_status()
        assert result == expected_response

    def test_get_system_status_invalid_response(self, note_manager):
        """Test handling of invalid system status response."""
        note_manager._client._request.return_value = {"status": "operational"}  # Missing required fields
        
        with pytest.raises(ValidationError):
            note_manager.get_system_status()
