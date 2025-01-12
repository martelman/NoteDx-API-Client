import pytest
from unittest.mock import patch, MagicMock
import requests
import os

from notedx_sdk.exceptions import (
    NotFoundError, JobNotFoundError, ValidationError, 
    MissingFieldError, InvalidFieldError, NetworkError,
    JobError, BadRequestError
)

@pytest.fixture
def mock_open(mocker):
    """Mock open function for file operations."""
    return mocker.patch('builtins.open', mocker.mock_open(read_data=b'test'))

@pytest.fixture
def mock_client():
    """Mock client with API key."""
    from notedx_sdk import NoteDxClient
    client = NoteDxClient(
        api_key="test-api-key",
        base_url="https://api.test.notedx.com"
    )
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

class TestNoteManager:
    """Test cases for NoteManager class."""

    def test_validate_audio_file_success(self, mock_client, mock_open):
        """Test successful audio file validation."""
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            mock_client.notes._validate_audio_file("test.mp3")

    def test_process_audio_success(self, mock_client, mock_response, mock_job_id, mock_open):
        """Test successful audio processing."""
        mock_response.update({
            "job_id": mock_job_id,
            "presigned_url": "https://example.com/upload"
        })
        mock_client.notes._request = MagicMock(return_value=mock_response)
        
        with patch('os.path.isfile') as mock_isfile, \
             patch('requests.put') as mock_put:
            mock_isfile.return_value = True
            mock_put.return_value.status_code = 200
            
            response = mock_client.notes.process_audio(
                file_path="test.mp3",
                visit_type="initialEncounter",
                recording_type="dictation",
                patient_consent=True,
                template="primaryCare"
            )
            
            assert response["job_id"] == mock_job_id
            assert response["presigned_url"] == "https://example.com/upload"

    def test_regenerate_note_success(self, mock_client, mock_response, mock_job_id):
        """Test successful note regeneration."""
        mock_response.update({
            "job_id": mock_job_id,
            "status": "pending"
        })
        mock_client.notes._request = MagicMock(return_value=mock_response)
        
        response = mock_client.notes.regenerate_note(
            job_id=mock_job_id,
            template="primaryCare"
        )
        
        assert response["job_id"] == mock_job_id
        assert response["status"] == "pending"

    def test_fetch_status_success(self, mock_client, mock_response, mock_job_id):
        """Test successful status fetch."""
        mock_response.update({
            "job_id": mock_job_id,
            "status": "completed"
        })
        mock_client.notes._request = MagicMock(return_value=mock_response)
        
        response = mock_client.notes.fetch_status(mock_job_id)
        assert response["job_id"] == mock_job_id
        assert response["status"] == "completed"

    def test_fetch_note_success(self, mock_client, mock_response, mock_job_id):
        """Test successful note fetch."""
        mock_response.update({
            "job_id": mock_job_id,
            "note": "Test medical note content"
        })
        mock_client.notes._request = MagicMock(return_value=mock_response)
        
        response = mock_client.notes.fetch_note(mock_job_id)
        assert response["job_id"] == mock_job_id
        assert response["note"] == "Test medical note content"

    def test_fetch_transcript_success(self, mock_client, mock_response, mock_job_id):
        """Test successful transcript fetch."""
        mock_response.update({
            "job_id": mock_job_id,
            "transcript": "Test transcript content"
        })
        mock_client.notes._request = MagicMock(return_value=mock_response)
        
        response = mock_client.notes.fetch_transcript(mock_job_id)
        assert response["job_id"] == mock_job_id
        assert response["transcript"] == "Test transcript content" 