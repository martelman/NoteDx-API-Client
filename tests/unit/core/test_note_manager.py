import pytest
from unittest.mock import patch, MagicMock

from src.notedx_sdk import NoteDxClient
from src.notedx_sdk.exceptions import BadRequestError, NotFoundError, PaymentRequiredError, ValidationError, JobError


@pytest.fixture
def mock_open(mocker):
    """Mock open function for file operations."""
    return mocker.patch('builtins.open', mocker.mock_open(read_data=b'test'))

@pytest.fixture
def mock_client():
    """Mock client with API key."""
    client = NoteDxClient(api_key="test-api-key")
    return client

@pytest.fixture
def mock_job_id():
    """Mock job ID for testing."""
    return "test-job-id"

@pytest.fixture
def mock_response():
    """Base mock response."""
    return {
        "message": "Success",
        "status": "pending"
    }

@pytest.mark.unit
class TestNoteManager:
    @patch('os.path.isfile')
    @patch('builtins.open')
    def test_validate_audio_file_success(self, mock_open, mock_isfile, mock_client):
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        mock_client.notes._validate_audio_file("test.mp3")

    @patch('os.path.isfile')
    def test_validate_audio_file_missing_path(self, mock_isfile, mock_client):
        mock_isfile.return_value = False
        with pytest.raises(ValidationError) as exc_info:
            mock_client.notes._validate_audio_file("test.mp3")
        assert "Audio file not found" in str(exc_info.value)

    @patch('os.path.isfile')
    @patch('builtins.open')
    def test_validate_audio_file_invalid_format(self, mock_open, mock_isfile, mock_client):
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        with pytest.raises(ValidationError) as exc_info:
            mock_client.notes._validate_audio_file("test.txt")
        assert "Unsupported audio format" in str(exc_info.value)

    @patch('os.path.isfile')
    @patch('builtins.open')
    @patch('requests.put')
    @patch('requests.request')
    def test_process_audio_success(self, mock_request, mock_put, mock_open, mock_isfile, mock_client):
        # Mock file validation
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'job_id': 'test-job-id',
            'presigned_url': 'https://example.com/upload'
        }
        mock_request.return_value = mock_response

        # Mock upload response
        mock_put_response = MagicMock()
        mock_put_response.status_code = 200
        mock_put.return_value = mock_put_response

        response = mock_client.notes.process_audio(
            file_path="test.mp3",
            template="wfw",  # Special template
            lang="en"
        )
        assert response['job_id'] == 'test-job-id'
        assert response['presigned_url'] == 'https://example.com/upload'

    @patch('os.path.isfile')
    @patch('builtins.open')
    @patch('requests.request')
    def test_process_audio_missing_field(self, mock_request, mock_open, mock_isfile, mock_client):
        # Mock file validation
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Missing required field: template"
        mock_request.return_value = mock_response

        with pytest.raises(BadRequestError) as exc_info:
            mock_client.notes.process_audio(
                file_path="test.mp3",
                template="primaryCare",  # Add valid template
                visit_type="initialEncounter",
                recording_type="dictation",
                lang="en"
            )
        assert "Missing required field: template" in str(exc_info.value)

    @patch('os.path.isfile')
    @patch('builtins.open')
    @patch('requests.request')
    def test_process_audio_invalid_field(self, mock_request, mock_open, mock_isfile, mock_client):
        # Mock file validation
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid value for template. Must be one of: primaryCare, er, psychiatry, surgicalSpecialties, medicalSpecialties, nursing, radiology, procedures, letter, social, wfw, smartInsert"
        mock_request.return_value = mock_response

        with pytest.raises(BadRequestError) as exc_info:
            mock_client.notes.process_audio(
                file_path="test.mp3",
                template="primaryCare",  # Use valid template to pass validation
                visit_type="initialEncounter",
                recording_type="dictation",
                lang="en"
            )
        assert "Invalid value for template" in str(exc_info.value)

    @patch('os.path.isfile')
    @patch('builtins.open')
    @patch('requests.request')
    def test_process_audio_payment_required(self, mock_request, mock_open, mock_isfile, mock_client):
        # Mock file validation
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.text = "Payment required: Please upgrade your plan"
        mock_request.return_value = mock_response

        with pytest.raises(PaymentRequiredError) as exc_info:
            mock_client.notes.process_audio(
                file_path="test.mp3",
                template="wfw",
                lang="en"
            )
        assert "Payment required: Please upgrade your plan" in str(exc_info.value)

    @patch('requests.request')
    def test_regenerate_note_success(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'job_id': 'new-job-id'
        }
        mock_request.return_value = mock_response

        response = mock_client.notes.regenerate_note('original-job-id')
        assert response['job_id'] == 'new-job-id'

    @patch('requests.request')
    def test_regenerate_note_no_transcript(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Source job has no transcript"
        mock_request.return_value = mock_response

        with pytest.raises(JobError) as exc_info:
            mock_client.notes.regenerate_note('job-id')
        assert "Source job has no transcript" in str(exc_info.value)

    @patch('requests.request')
    def test_fetch_status_success(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'completed',
            'message': None
        }
        mock_request.return_value = mock_response

        response = mock_client.notes.fetch_status('job-id')
        assert response['status'] == 'completed'

    @patch('requests.request')
    def test_fetch_status_not_found(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Job not found"
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError) as exc_info:
            mock_client.notes.fetch_status('invalid-job')
        assert "Job not found" in str(exc_info.value)

    @patch('requests.request')
    def test_fetch_note_success(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'note': 'Generated note content',
            'job_id': 'job-id',
            'noteTitle': 'Note Title'
        }
        mock_request.return_value = mock_response

        response = mock_client.notes.fetch_note('job-id')
        assert response['note'] == 'Generated note content'
        assert response['noteTitle'] == 'Note Title'

    @patch('requests.request')
    def test_fetch_note_not_completed(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Note generation not completed"
        mock_request.return_value = mock_response

        with pytest.raises(JobError) as exc_info:
            mock_client.notes.fetch_note('job-id')
        assert "Note generation not completed" in str(exc_info.value)

    @patch('requests.request')
    def test_fetch_transcript_success(self, mock_request, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'transcript': 'Transcribed text content',
            'job_id': 'job-id'
        }
        mock_request.return_value = mock_response

        response = mock_client.notes.fetch_transcript('job-id')
        assert response['transcript'] == 'Transcribed text content' 