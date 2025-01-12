from typing import Optional, Dict, Any, Literal

import os
import requests
import logging
from ..exceptions import (
    NoteDxError,
    AuthenticationError,
    AuthorizationError,
    PaymentRequiredError,
    InactiveAccountError,
    NetworkError,
    ValidationError,
    MissingFieldError,
    InvalidFieldError,
    BadRequestError,
    UploadError,
    NotFoundError,
    JobNotFoundError,
    JobError,
    RateLimitError,
    InternalServerError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)

# Valid values for fields
VALID_VISIT_TYPES = ['initialEncounter', 'followUp']
VALID_RECORDING_TYPES = ['dictation', 'conversation']
VALID_LANGUAGES = ['en', 'fr']
VALID_TEMPLATES = [
    'primaryCare', 'er', 'psychiatry', 'surgicalSpecialties',
    'medicalSpecialties', 'nursing', 'radiology', 'procedures',
    'letter', 'social', 'wfw','smartInsert'
]

# Valid audio formats and their MIME types
VALID_AUDIO_FORMATS = {
    '.mp3': 'audio/mpeg',
    '.mp4': 'audio/mp4',
    '.mp2': 'audio/mpeg',
    '.m4a': 'audio/mp4',
    '.aac': 'audio/aac',
    '.wav': 'audio/wav',
    '.flac': 'audio/flac',
    '.pcm': 'audio/x-pcm',
    '.ogg': 'audio/ogg',
    '.opus': 'audio/opus',
    '.webm': 'audio/webm'
}

class NoteManager:
    """
    Handles core note generation operations for the NoteDx API.
    
    This class provides methods for:
    - Audio file processing
    - Note generation and regeneration
    - Job status tracking
    - Result retrieval
    """
    
    _API_BASE_URL = "https://36c498e49l.execute-api.ca-central-1.amazonaws.com/dev"
    
    def __init__(self, client):
        """
        Initialize the note manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client
        if not self._client._api_key:
            raise AuthenticationError("API key is required for note generation operations")

    def _request(self, method: str, endpoint: str, data: Any = None, params: Dict[str, Any] = None, timeout: int = 60) -> Dict[str, Any]:
        """
        Override parent client's _request method to ensure API key authentication for note generation.
        All note generation endpoints use API key authentication exclusively.
        """
        if not self._client._api_key:
            raise AuthenticationError("API key is required for note generation operations")

        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self._client._api_key
        }

        try:
            response = requests.request(
                method,
                f"{self._API_BASE_URL}/{endpoint}",
                json=data if data else None,
                params=params,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 403:
                raise AuthorizationError("API key does not have required permissions")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self._client._handle_request_error(e)

    def _validate_input(self, **kwargs) -> None:
        """
        Validate input parameters against API requirements.
        
        Special handling for templates:
        - For 'wfw' (word for word) and 'smartInsert' templates:
          * Only language ('lang') is required
          * visit_type and recording_type are not required
        - For all other templates:
          * All fields (visit_type, recording_type, lang, template) are required
          * Patient consent is required for conversation mode
        """
        template = kwargs.get('template')
        
        # Special case for 'wfw' and 'smartInsert' templates
        if template in ['wfw', 'smartInsert']:
            # Only validate language and template
            if template not in VALID_TEMPLATES:
                raise InvalidFieldError(
                    'template',
                    f"Invalid value for template. Must be one of: {', '.join(VALID_TEMPLATES)}"
                )
            if 'lang' not in kwargs or kwargs['lang'] not in VALID_LANGUAGES:
                raise InvalidFieldError(
                    'lang',
                    f"Invalid value for lang. Must be one of: {', '.join(VALID_LANGUAGES)}"
                )
            return

        # Standard validation for other templates
        required_fields = {
            'visit_type': VALID_VISIT_TYPES,
            'recording_type': VALID_RECORDING_TYPES,
            'lang': VALID_LANGUAGES,
            'template': VALID_TEMPLATES
        }
        
        for field, valid_values in required_fields.items():
            value = kwargs.get(field)
            if value is None:
                raise MissingFieldError(field)
            if value not in valid_values:
                raise InvalidFieldError(
                    field,
                    f"Invalid value for {field}. Must be one of: {', '.join(valid_values)}"
                )
        
        # Special validation for conversation mode
        if kwargs.get('recording_type') == 'conversation' and not kwargs.get('patient_consent'):
            raise ValidationError(
                "Patient consent is required for conversation mode",
                field="patient_consent",
                details={"recording_type": "conversation"}
            )

    def process_audio(
        self,
        file_path: str,
        visit_type: Literal['initialEncounter', 'followUp'],
        recording_type: Literal['dictation', 'conversation'],
        patient_consent: bool,
        lang: Literal['en', 'fr'] = 'en',
        output_language: Optional[Literal['en', 'fr']] = None,
        template: Optional[Literal['primaryCare', 'er', 'psychiatry', 'surgicalSpecialties', 
                                 'medicalSpecialties', 'nursing', 'radiology', 'procedures', 
                                 'letter', 'social', 'wfw', 'smartInsert']] = None,
        custom: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an audio file to generate a medical note.

        This method handles the complete flow of:
        1. Validating the audio file
        2. Getting a presigned URL for upload
        3. Uploading the file
        4. Initiating note generation

        Special Template Handling:
        - For 'wfw' (word for word) and 'smartInsert' templates:
          * Only file_path and lang are required
          * visit_type and recording_type are optional and will be ignored
          * patient_consent is not required
        - For all other templates:
          * file_path, visit_type, recording_type, and lang are required
          * patient_consent is required for conversation mode

        Args:
            file_path: Path to the audio file. Supported formats:
                - .mp3, .mp2 (audio/mpeg)
                - .mp4, .m4a (audio/mp4)
                - .aac (audio/aac)
                - .wav (audio/wav)
                - .flac (audio/flac)
                - .pcm (audio/x-pcm)
                - .ogg (audio/ogg)
                - .opus (audio/opus)
                - .webm (audio/webm)
            visit_type: Type of medical visit (optional for 'wfw' or 'smartInsert' templates)
                - 'initialEncounter': First visit with patient
                - 'followUp': Subsequent visit
            recording_type: Type of audio recording (optional for 'wfw' or 'smartInsert' templates)
                - 'dictation': Single speaker dictation
                - 'conversation': Multi-speaker conversation
            patient_consent: Whether patient consent was obtained
                           Required for conversation mode, optional for 'wfw' or 'smartInsert'
            lang: Source language of the audio (required for all templates)
                - 'en': English (default)
                - 'fr': French
            output_language: Target language for the note
                - None: Same as source language
                - 'en': English
                - 'fr': French
            template: Medical note template to use
                Standard templates (require visit_type and recording_type):
                - 'primaryCare': Primary care visit
                - 'er': Emergency room visit
                - 'psychiatry': Psychiatric evaluation
                - 'surgicalSpecialties': Surgical specialties
                - 'medicalSpecialties': Medical specialties
                - 'nursing': Nursing notes
                - 'radiology': Radiology reports
                - 'procedures': Procedure notes
                - 'letter': Medical letters
                - 'social': Social worker notes
                Special templates (only require file_path and lang):
                - 'wfw': Word for word dictation
                - 'smartInsert': Smart insert mode
            custom: Optional custom parameters for note generation
                    the dict can contain the following keys:
                    - template: the template to use for the note
                    - context: additionnal context about the patient you can include (e.g. age, gender, medical history, past medical history, etc. It will be passed to the model in the prompt.)

        Returns:
            Dict containing:
            - job_id: Unique identifier for the job
            - presigned_url: URL used for file upload
            - status: Initial job status
            - Additional fields as per API response

        Raises:
            ValidationError: If:
                - File doesn't exist or isn't readable
                - Invalid audio format
                - Invalid parameters provided
                - Required fields missing based on template type:
                  * Standard templates: visit_type, recording_type, lang required
                  * Special templates (wfw/smartInsert): only file_path and lang required
                - Patient consent missing for conversation mode (except wfw/smartInsert)
            UploadError: If file upload fails
            NetworkError: If connection issues occur
            BadRequestError: If API rejects the request
            AuthenticationError: If authentication fails
            PaymentRequiredError: If payment is required
            InactiveAccountError: If account is inactive
            InternalServerError: If server error occurs

        Example:
            >>> # Standard template usage (all fields required)
            >>> response = client.notes.process_audio(
            ...     file_path="visit.mp3",
            ...     visit_type="initialEncounter",
            ...     recording_type="conversation",
            ...     patient_consent=True,
            ...     lang="en",
            ...     template="primaryCare"
            ... )
            >>> 
            >>> # Word for word template usage (simplified)
            >>> response = client.notes.process_audio(
            ...     file_path="dictation.mp3",
            ...     lang="en",
            ...     template="wfw"
            ... )
            >>> job_id = response["job_id"]
            >>> # Use job_id to check status and fetch results

        Note:
            - The audio file should be a clear recording for best results
            - For conversation mode, ensure clear separation between speakers
            - Large files (>100MB) may take longer to upload
            - The job_id should be stored to fetch results later
            - Template choice determines required fields:
              * Standard templates need all fields
              * 'wfw' and 'smartInsert' only need file_path and lang
        """
        # Validate file
        self._validate_audio_file(file_path)

        # Validate input parameters
        self._validate_input(
            visit_type=visit_type,
            recording_type=recording_type,
            lang=lang,
            template=template,
            patient_consent=patient_consent
        )

        # Prepare request data
        data = {
            'visit_type': visit_type,
            'recording_type': recording_type,
            'lang': lang,
            'consent': str(patient_consent).lower()
        }

        if output_language:
            if output_language not in VALID_LANGUAGES:
                raise InvalidFieldError(
                    'output_language',
                    f"Invalid value for output_language. Must be one of: {', '.join(VALID_LANGUAGES)}"
                )
            data['output_language'] = output_language
            
        if template:
            data['template'] = template
            
        if custom:
            data['custom'] = custom

        try:
            # Get presigned URL and job_id
            response = self._request("POST", "process-audio", data=data)
            
            job_id = response.get('job_id')
            presigned_url = response.get('presigned_url')
            
            if not presigned_url or not job_id:
                raise ValidationError(
                    "Invalid API response: missing presigned_url or job_id",
                    details={"response": response}
                )

            # Upload file using presigned URL
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                mime_type = VALID_AUDIO_FORMATS[file_ext]
                
                with open(file_path, 'rb') as f:
                    upload_response = requests.put(
                        presigned_url,
                        data=f,
                        headers={'Content-Type': mime_type},
                        timeout=60
                    )
                    upload_response.raise_for_status()
                logger.info(f"Successfully uploaded file for job {job_id}")
            except Exception as e:
                self._handle_upload_error(e, job_id)

            return response

        except (
            NoteDxError,  # Base exception
            AuthenticationError,  # 401 - Invalid credentials
            AuthorizationError,  # 403 - Permission denied
            PaymentRequiredError,  # 402 - Payment required
            InactiveAccountError,  # 403 - Account inactive
            RateLimitError  # 429 - Too many requests
        ):
            # Let API-specific errors propagate as is
            raise
        except Exception as e:
            logger.error(f"Error in process_audio: {str(e)}")
            raise InternalServerError(f"Unexpected error: {str(e)}")

    def regenerate_note(
        self,
        job_id: str,
        template: Optional[Literal['primaryCare', 'er', 'psychiatry', 'surgicalSpecialties', 
                                 'medicalSpecialties', 'nursing', 'radiology', 'procedures', 
                                 'letter', 'social', 'wfw', 'smartInsert']] = None,
        output_language: Optional[Literal['en', 'fr']] = None,
        custom: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate a medical note from an existing transcript with different parameters.

        This method allows you to:
        1. Generate a new note from an existing transcript
        2. Use a different template or output language
        3. Modify generation parameters without re-uploading audio

        Args:
            job_id: ID of the original job to regenerate from
                   Must be a completed job with a transcript
            template: Medical note template to use
                - 'primaryCare': Primary care visit
                - 'er': Emergency room visit
                - 'psychiatry': Psychiatric evaluation
                - 'surgicalSpecialties': Surgical specialties
                - 'medicalSpecialties': Medical specialties
                - 'nursing': Nursing notes
                - 'radiology': Radiology reports
                - 'procedures': Procedure notes
                - 'letter': Medical letters
                - 'social': Social worker notes
                - 'wfw': Word for word dictation
                - 'smartInsert': Smart insert mode
            output_language: Target language for the note
                - None: Same as source language
                - 'en': English
                - 'fr': French
            custom: Optional custom parameters for note generation
                   See API documentation for available options

        Returns:
            Dict containing:
            - job_id: New job ID for the regenerated note
            - status: Initial job status
            - Additional fields as per API response

        Raises:
            ValidationError: If job_id is invalid
            NotFoundError: If source job is not found
            JobError: If source job has no transcript
            BadRequestError: If API rejects the request
            AuthenticationError: If authentication fails
            PaymentRequiredError: If payment is required
            InactiveAccountError: If account is inactive
            NetworkError: If connection issues occur

        Example:
            >>> # First, get original job_id from process_audio
            >>> response = client.notes.regenerate_note(
            ...     job_id="original-job-id",
            ...     template="er",  # Change template
            ...     output_language="fr"  # Translate to French
            ... )
            >>> new_job_id = response["job_id"]
            >>> # Use new_job_id to fetch regenerated note

        Note:
            - The original transcript is reused, no need to re-upload audio
            - Processing is usually faster than the original note generation
            - All parameters except job_id are optional
            - If no parameters are changed, generates an identical note
        """
        if not job_id:
            raise MissingFieldError("job_id")

        data = {
            'job_id': job_id
        }

        if template:
            if template not in VALID_TEMPLATES:
                raise InvalidFieldError(
                    'template',
                    f"Invalid template value. Must be one of: {', '.join(VALID_TEMPLATES)}"
                )
            data['template'] = template
            
        if output_language:
            if output_language not in VALID_LANGUAGES:
                raise InvalidFieldError(
                    'output_language',
                    f"Invalid value for output_language. Must be one of: {', '.join(VALID_LANGUAGES)}"
                )
            data['output_language'] = output_language
            
        if custom:
            data['custom'] = custom

        try:
            return self._request("POST", "regenerate-note", data=data)
        except NotFoundError:
            raise JobNotFoundError(job_id)
        except BadRequestError as e:
            if "no transcript" in str(e).lower():
                raise JobError(
                    "Source job has no transcript",
                    job_id=job_id,
                    details=e.details
                )
            raise
        except (
            NoteDxError,
            AuthenticationError,
            AuthorizationError,
            PaymentRequiredError,
            InactiveAccountError,
            RateLimitError
        ):
            raise
        except Exception as e:
            logger.error(f"Error regenerating note from job {job_id}: {str(e)}")
            raise InternalServerError(f"Unexpected error: {str(e)}")

    def fetch_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the current status and progress of a note generation job.

        The job can be in one of these states:
        - 'pending': Job created, waiting for file upload
        - 'queued': File uploaded, waiting for processing
        - 'transcribing': Audio file is being transcribed
        - 'transcribed': Transcript ready, generating note
        - 'completed': Note generation finished successfully
        - 'error': Job failed with an error

        Args:
            job_id: The ID of the job to check
                   Obtained from process_audio or regenerate_note

        Returns:
            Dict containing:
            - status: Current job status (see states above)
            - message: Optional status message or error details
            - progress: Optional progress information
            - Additional fields as per API response

        Raises:
            ValidationError: If job_id is invalid
            NotFoundError: If job is not found
            AuthenticationError: If authentication fails
            NetworkError: If connection issues occur

        Example:
            >>> status = client.notes.fetch_status("job-id")
            >>> if status["status"] == "completed":
            ...     note = client.notes.fetch_note("job-id")
            >>> elif status["status"] == "error":
            ...     print(f"Error: {status['message']}")

        Note:
            - Polling interval should be at least 5 seconds
            - Jobs typically complete within 2-3 minutes
            - Error status includes detailed error message
            - Status history is preserved for 48 hours
        """
        if not job_id:
            raise MissingFieldError("job_id")
        
        try:
            return self._request("GET", f"status/{job_id}")
        except NotFoundError:
            raise JobNotFoundError(job_id)
        except (
            NoteDxError,
            AuthenticationError,
            AuthorizationError,
            PaymentRequiredError,
            InactiveAccountError,
            RateLimitError
        ):
            raise
        except Exception as e:
            logger.error(f"Error fetching status for job {job_id}: {str(e)}")
            raise InternalServerError(f"Unexpected error: {str(e)}")

    def fetch_note(self, job_id: str) -> Dict[str, Any]:
        """
        Fetch the generated medical note for a completed job.

        This method retrieves the final note after processing is complete.
        The note includes:
        - Patient consent statement (if applicable)
        - Structured medical note based on template
        - Optional note title
        - Source/target language information

        Args:
            job_id: The ID of the job to fetch the note for
                   Job must be in 'completed' status

        Returns:
            Dict containing:
            - note: The generated medical note text
            - noteTitle: Optional title for the note
            - job_id: The job ID (for reference)
            - Additional fields as per API response

        Raises:
            ValidationError: If job_id is invalid
            NotFoundError: If job or note is not found
            JobError: If note generation is not completed
            AuthenticationError: If authentication fails
            NetworkError: If connection issues occur

        Example:
            >>> # First check status
            >>> status = client.notes.fetch_status("job-id")
            >>> if status["status"] == "completed":
            ...     result = client.notes.fetch_note("job-id")
            ...     print(f"Title: {result['noteTitle']}")
            ...     print(f"Note: {result['note']}")

        Note:
            - Always check job status before fetching note
            - Notes are available for 48 hours after completion
            - Notes include patient consent if provided
            - The note format follows the selected template
        """
        if not job_id:
            raise MissingFieldError("job_id")
        
        try:
            return self._request("GET", f"fetch-note/{job_id}")
        except NotFoundError:
            raise JobNotFoundError(job_id)
        except BadRequestError as e:
            if "not completed" in str(e).lower():
                raise JobError(
                    "Note generation not completed",
                    job_id=job_id,
                    status="incomplete",
                    details=e.details
                )
            raise
        except (
            NoteDxError,
            AuthenticationError,
            AuthorizationError,
            PaymentRequiredError,
            InactiveAccountError,
            RateLimitError
        ):
            raise
        except Exception as e:
            logger.error(f"Error fetching note for job {job_id}: {str(e)}")
            raise InternalServerError(f"Unexpected error: {str(e)}")

    def fetch_transcript(self, job_id: str) -> Dict[str, Any]:
        """
        Fetch the raw transcript for a job after audio processing.

        The transcript represents the raw text from audio processing,
        before any medical note generation. Useful for:
        - Verifying audio processing accuracy
        - Debugging note generation issues
        - Keeping raw transcripts for records

        Args:
            job_id: The ID of the job to fetch the transcript for
                   Job must be in 'transcribed' or 'completed' status

        Returns:
            Dict containing:
            - transcript: The raw transcript text
            - job_id: The job ID (for reference)
            - Additional fields as per API response

        Raises:
            ValidationError: If job_id is invalid
            NotFoundError: If job or transcript is not found
            JobError: If transcription is not completed
            AuthenticationError: If authentication fails
            NetworkError: If connection issues occur

        Example:
            >>> # Useful for verification
            >>> transcript = client.notes.fetch_transcript("job-id")
            >>> print(f"Raw text: {transcript['transcript']}")

        Note:
            - Available after transcription, before note generation
            - Preserved for 48 hours after job completion
            - Includes all recognized speech from audio
            - May contain speaker labels in conversation mode
        """
        if not job_id:
            raise MissingFieldError("job_id")
        
        try:
            return self._request("GET", f"fetch-transcript/{job_id}")
        except NotFoundError:
            raise JobNotFoundError(job_id)
        except BadRequestError as e:
            if "not transcribed" in str(e).lower():
                raise JobError(
                    "Transcription not completed",
                    job_id=job_id,
                    status="not_transcribed",
                    details=e.details
                )
            raise
        except (
            NoteDxError,
            AuthenticationError,
            AuthorizationError,
            PaymentRequiredError,
            InactiveAccountError,
            RateLimitError
        ):
            raise
        except Exception as e:
            logger.error(f"Error fetching transcript for job {job_id}: {str(e)}")
            raise InternalServerError(f"Unexpected error: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and health information.

        Returns:
            Dict containing:
            - status: Overall system status
            - services: Status of individual services
            - latency: Current processing latencies
            - Additional fields as per API response

        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If connection issues occur
            InternalServerError: If server status check fails

        Example:
            >>> status = client.notes.get_system_status()
            >>> print(f"System status: {status['status']}")
            >>> print(f"Average latency: {status['latency']['avg']}ms")

        Note:
            - Updated every minute
            - Includes all system components
            - Useful for monitoring and debugging
            - No authentication required
        """
        try:
            return self._request("GET", "system/status")
        except (
            NoteDxError,
            AuthenticationError,
            AuthorizationError,
            RateLimitError
        ):
            raise
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            raise ServiceUnavailableError("System status check failed", details={"error": str(e)})

    def _validate_audio_file(self, file_path: str) -> None:
        """
        Validate audio file existence, readability, and format.
        
        Args:
            file_path: Path to the audio file
            
        Raises:
            MissingFieldError: If file_path is empty
            ValidationError: If:
                - File doesn't exist
                - File isn't readable
                - File format is not supported
        """
        if not file_path:
            raise MissingFieldError("file_path")
            
        if not os.path.isfile(file_path):
            raise ValidationError(
                f"Audio file not found: {file_path}",
                field="file_path",
                details={"path": file_path}
            )

        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in VALID_AUDIO_FORMATS:
            raise ValidationError(
                f"Unsupported audio format: {file_ext}. Supported formats: {', '.join(VALID_AUDIO_FORMATS.keys())}",
                field="file_path",
                details={
                    "path": file_path,
                    "extension": file_ext,
                    "supported_formats": list(VALID_AUDIO_FORMATS.keys())
                }
            )

        try:
            with open(file_path, 'rb') as f:
                # Just test if we can read it
                f.read(1)
        except Exception as e:
            raise ValidationError(
                f"Cannot read audio file: {str(e)}",
                field="file_path",
                details={"path": file_path, "error": str(e)}
            )

    def _handle_upload_error(self, e: Exception, job_id: str) -> None:
        """Handle file upload errors with appropriate exception types."""
        if isinstance(e, requests.ConnectionError):
            raise NetworkError(
                f"Connection error during file upload: {str(e)}",
                details={"job_id": job_id}
            )
        elif isinstance(e, requests.Timeout):
            raise NetworkError(
                f"Timeout during file upload: {str(e)}",
                details={"job_id": job_id}
            )
        elif isinstance(e, requests.RequestException):
            raise UploadError(
                f"Failed to upload file: {str(e)}",
                job_id=job_id
            )
        else:
            raise UploadError(
                f"Unexpected error during upload: {str(e)}",
                job_id=job_id
            ) 