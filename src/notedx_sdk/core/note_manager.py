from typing import Dict, Any, Literal, Optional, List, TYPE_CHECKING, Union
from logging import Handler
import os
import requests
import logging
import time
from ..exceptions import (
    AuthenticationError,
    AuthorizationError,
    NoteDxError,
    PaymentRequiredError,
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

if TYPE_CHECKING:
    from ..client import NoteDxClient

# Initialize SDK logger with null handler by default
logger = logging.getLogger("notedx_sdk")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)

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
    """Manages medical note generation from audio files using the NoteDx API.

    This class provides a high-level interface for:

    - Converting audio recordings to medical notes
    - Managing note generation jobs
    - Retrieving generated notes and transcripts
    - Monitoring system status

    The NoteManager handles all API authentication and error handling,
    making it easy to integrate medical note generation into your application.

    Example:
        ```python
        >>> from notedx_sdk import NoteDxClient
        >>> client = NoteDxClient(api_key="your-api-key")
        >>> note_manager = client.notes
        >>> 
        >>> # Generate a medical note from an audio file
        >>> response = note_manager.process_audio(
        ...     file_path="patient_visit.mp3",
        ...     visit_type="initialEncounter",
        ...     recording_type="dictation",
        ...     template="primaryCare"
        ... )
        >>> job_id = response["job_id"]
        >>> 
        >>> # Check status and get the note when ready
        >>> status = note_manager.fetch_status(job_id)
        >>> if status["status"] == "completed":
        ...     note = note_manager.fetch_note(job_id)
        ...     print(note["note"])
        ```
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'api_base_url': "https://api.notedx.io/v1",
        'request_timeout': 60,
        'max_retries': 3,
        'retry_delay': 1,  # seconds
        'retry_max_delay': 30,  # seconds
        'retry_on_status': [408, 429, 500, 502, 503, 504]
    }
    
    def __init__(self, client: "NoteDxClient") -> None:
        """Initialize the NoteManager.
        
        Args:
            client: The NoteDxClient instance.
        """
        self._client = client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("Initialized NoteManager")

    def set_logger(self, level: Union[int, str], handler: Optional[Handler] = None) -> None:
        """Set the logger level and handler.
        
        Args:
            level: The logging level (e.g., logging.INFO).
            handler: Optional logging handler.
        """
        self.logger.setLevel(level)
        if handler:
            self.logger.addHandler(handler)

    @classmethod
    def configure_logging(cls, level: Union[int, str] = logging.INFO, handler: Optional[Handler] = None) -> None:
        """Configure logging for the SDK.

        Args:
            level: The logging level (e.g., logging.DEBUG, logging.INFO)
            handler: Optional logging handler to add. If None, logs to console.

        Example:
            ```python
            >>> # Enable debug logging to console
            >>> NoteManager.configure_logging(logging.DEBUG)
            >>> 
            >>> # Log to a file
            >>> file_handler = logging.FileHandler('notedx.log')
            >>> NoteManager.configure_logging(logging.INFO, file_handler)
            ```
        """
        logger = logging.getLogger("notedx_sdk")
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Add handler
        if handler is None:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(level)

    def _request(self, method: str, endpoint: str, data: Any = None, params: Dict[str, Any] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Make an authenticated request to the NoteDx API.

        This method handles:
        - API key authentication
        - Request retries with exponential backoff
        - Error response parsing and conversion to exceptions
        - Request/response logging (at DEBUG level)
        - Timeout configuration

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL parameters
            timeout: Request timeout (overrides config)

        Returns:
            API response data as dictionary

        Raises:
            Various NoteDxError subclasses based on response
        """
        if not self._client._api_key:
            raise AuthenticationError("API key is required for note generation operations")

        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self._client._api_key
        }

        url = f"{self._config['api_base_url']}/{endpoint}"
        timeout = timeout or self._config['request_timeout']
        retries = 0
        delay = self._config['retry_delay']

        while True:
            try:
                self.logger.debug(
                    "Making %s request to %s",
                    method,
                    url,
                    extra={
                        'params': params,
                        'headers': {k: '***' if k == 'x-api-key' else v 
                                  for k, v in headers.items()}
                    }
                )

                response = requests.request(
                    method,
                    url,
                    json=data if data else None,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
                
                self.logger.debug(
                    "Received response: %s %s",
                    response.status_code,
                    response.text[:1000] + '...' if len(response.text) > 1000 else response.text
                )
                
                # Handle various error responses
                if response.status_code == 401:
                    raise AuthenticationError(f"Invalid API key: {response.text}")
                elif response.status_code == 403:
                    raise AuthorizationError(f"API key does not have required permissions: {response.text}")
                elif response.status_code == 402:
                    raise PaymentRequiredError(f"Payment required: {response.text}")
                elif response.status_code == 429:
                    raise RateLimitError(f"Rate limit exceeded: {response.text}")
                elif response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {response.text}")
                elif response.status_code == 400:
                    raise BadRequestError(response.text)
                elif response.status_code >= 500:
                    # Only retry on server errors if we haven't exceeded max retries
                    if (response.status_code in self._config['retry_on_status'] and 
                        retries < self._config['max_retries']):
                        self.logger.warning(
                            "Request failed with %d, retrying in %d seconds (attempt %d/%d)",
                            response.status_code, delay, retries + 1, self._config['max_retries']
                        )
                        time.sleep(delay)
                        retries += 1
                        delay = min(delay * 2, self._config['retry_max_delay'])
                        continue
                    
                    raise InternalServerError(f"Server error: {response.text}")
                
                # If we get here, check for any other error status codes
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    self.logger.error("HTTP error occurred: %s", str(e))
                    raise NetworkError(f"HTTP error: {str(e)}")
                
                return response.json()
                
            except requests.exceptions.ConnectionError as e:
                self.logger.error("Connection error: %s", str(e))
                raise NetworkError(f"Connection error: {str(e)}")
            except requests.exceptions.Timeout as e:
                self.logger.error("Request timed out: %s", str(e))
                raise NetworkError(f"Request timed out: {str(e)}")
            except requests.exceptions.RequestException as e:
                self.logger.error("Request failed: %s", str(e))
                raise NetworkError(f"Request failed: {str(e)}")

    def _validate_input(self, **kwargs) -> None:
        """Validate input parameters against API requirements.

        Performs thorough validation of all input parameters:

            * Required fields based on template type
            * Field value validation
            * Special case handling for templates
            * Patient consent requirements

        Parameters:
            **kwargs: Input parameters to validate. See process_audio() for details.

        Raises:
            MissingFieldError: If required fields are missing
            InvalidFieldError: If field values are invalid
            ValidationError: For other validation errors
        """
        template = kwargs.get('template')
        
        # First validate template since it affects other validations
        if not template:
            self.logger.error("Missing required field: template")
            raise MissingFieldError("template")
            
        if template not in VALID_TEMPLATES:
            self.logger.error(
                "Invalid template value: %s. Valid values: %s",
                template, ', '.join(VALID_TEMPLATES)
            )
            raise InvalidFieldError(
                'template',
                f"Invalid value for template. Must be one of: {', '.join(VALID_TEMPLATES)}"
            )
        
        # Special case for 'wfw' and 'smartInsert' templates
        is_special_template = template in ['wfw', 'smartInsert']
        
        # Validate language (always required)
        lang = kwargs.get('lang')
        if not lang:
            self.logger.error("Missing required field: lang")
            raise MissingFieldError("lang")
            
        if lang not in VALID_LANGUAGES:
            self.logger.error(
                "Invalid lang value: %s. Valid values: %s",
                lang, ', '.join(VALID_LANGUAGES)
            )
            raise InvalidFieldError(
                'lang',
                f"Invalid value for lang. Must be one of: {', '.join(VALID_LANGUAGES)}"
            )
        
        # Validate output_language if provided
        if 'output_language' in kwargs and kwargs['output_language']:
            output_lang = kwargs['output_language']
            if output_lang not in VALID_LANGUAGES:
                self.logger.error(
                    "Invalid output_language: %s. Valid values: %s",
                    output_lang, ', '.join(VALID_LANGUAGES)
                )
                raise InvalidFieldError(
                    'output_language',
                    f"Invalid value for output_language. Must be one of: {', '.join(VALID_LANGUAGES)}"
                )
        
        # Skip visit_type and recording_type validation for special templates
        if not is_special_template:
            # Validate visit_type
            visit_type = kwargs.get('visit_type')
            if not visit_type:
                self.logger.error("Missing required field: visit_type")
                raise MissingFieldError("visit_type")
                
            if visit_type not in VALID_VISIT_TYPES:
                self.logger.error(
                    "Invalid visit_type: %s. Valid values: %s",
                    visit_type, ', '.join(VALID_VISIT_TYPES)
                )
                raise InvalidFieldError(
                    'visit_type',
                    f"Invalid value for visit_type. Must be one of: {', '.join(VALID_VISIT_TYPES)}"
                )
            
            # Validate recording_type
            recording_type = kwargs.get('recording_type')
            if not recording_type:
                self.logger.error("Missing required field: recording_type")
                raise MissingFieldError("recording_type")
                
            if recording_type not in VALID_RECORDING_TYPES:
                self.logger.error(
                    "Invalid recording_type: %s. Valid values: %s",
                    recording_type, ', '.join(VALID_RECORDING_TYPES)
                )
                raise InvalidFieldError(
                    'recording_type',
                    f"Invalid value for recording_type. Must be one of: {', '.join(VALID_RECORDING_TYPES)}"
                )
            
            # Only validate patient_consent for conversation mode
            if recording_type == 'conversation' and not kwargs.get('patient_consent'):
                self.logger.error(
                    "Patient consent required for conversation mode"
                )
                raise ValidationError(
                    "Patient consent is required for conversation mode",
                    field="patient_consent",
                    details={"recording_type": "conversation"}
                )

    def _calculate_optimal_chunk_size(self, file_size: int) -> int:
        """Calculate optimal chunk size based on file size.
        
        Args:
            file_size: Size of the file in bytes
            
        Returns:

            Optimal chunk size in bytes:
            - 5MB for files < 100MB
            - 10MB for files 100MB-250MB
            - 20MB for files > 250MB
        """
        MB = 1024 * 1024  # 1 MB in bytes
        
        if file_size < 100 * MB:
            return 5 * MB
        elif file_size < 250 * MB:
            return 10 * MB
        else:
            return 20 * MB

    def process_audio(
        self,
        file_path: str,
        visit_type: Optional[Literal['initialEncounter', 'followUp']] = None,
        recording_type: Optional[Literal['dictation', 'conversation']] = None,
        patient_consent: Optional[bool] = None,
        lang: Literal['en', 'fr'] = 'en',
        output_language: Optional[Literal['en', 'fr']] = None,
        template: Optional[Literal['primaryCare', 'er', 'psychiatry', 'surgicalSpecialties', 
                                 'medicalSpecialties', 'nursing', 'radiology', 'procedures', 
                                 'letter', 'social', 'wfw', 'smartInsert']] = None,
        custom: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None  # Now optional, will be calculated if not provided
    ) -> Dict[str, Any]:
        """Converts an audio recording into a medical note using the specified template.

        This method handles the complete flow of audio processing and note generation:

        1. Validates the audio file format and parameters
        2. Securely uploads the file
        3. Initiates the note generation process
        4. Returns a job ID for tracking progress

        Parameters:
            file_path: Path to the audio file.  
                Supported formats: `.mp3`, `.mp4`, `.m4a`, `.aac`, `.wav`, `.flac`, `.pcm`, `.ogg`, `.opus`, `.webm`

            visit_type: Type of medical visit (optional).  
                * `initialEncounter`: First visit with patient
                * `followUp`: Subsequent visit  
                Required for standard templates, optional for 'wfw'/'smartInsert'.

            recording_type: Type of audio recording (optional).  
                * `dictation`: Single speaker dictation
                * `conversation`: Multi-speaker conversation (requires patient_consent)  
                Required for standard templates, optional for 'wfw'/'smartInsert'.

            patient_consent: Whether patient consent was obtained (optional).  
                Required for conversation mode, optional otherwise.

            lang: Source language of the audio. Defaults to 'en'.  
                * `en`: English
                * `fr`: French

            output_language: Target language for the note (optional).  
                If not specified, uses the same language as the source.

            template: Medical note template to use.  
                The template determines how the audio content will be structured in the final note.

                **Standard templates** (require visit_type and recording_type):

                * `primaryCare` - Primary care visit for a general practitioner
                * `er` - Emergency room visit
                * `psychiatry` - Psychiatric evaluation
                * `surgicalSpecialties` - Surgical specialties (Any)
                * `medicalSpecialties` - Medical specialties (Any)
                * `nursing` - Nursing notes
                * `radiology` - Radiology reports
                * `procedures` - Procedure notes (small procedures, biopsies, outpatient surgeries, etc.)
                * `letter` - Medical letter to the referring physician
                * `social` - Social worker notes

                **Special templates** (only require file_path and lang):

                * `wfw` - Word for word transcription, supports inclusion of formatting and punctuation during dictation
                * `smartInsert` - Smart insertion mode

            custom: Additional parameters for note generation (optional).  
                Dictionary that can contain:

                * `context`: Additional patient context (history, demographics, medication, etc.)
                * `template`: A complete custom template as a string (SOAP note, other etc...)

            chunk_size: Size of upload chunks in bytes (optional).  
                Defaults to 1MB. Adjust for large files or slow connections.

        Returns:
            dict: A dictionary containing:

                * `job_id`: Unique identifier for tracking the job
                * `presigned_url`: URL for uploading the audio file
                * `status`: Initial job status

        Raises:
            ValidationError: If parameters are invalid or missing
            UploadError: If file upload fails
            AuthenticationError: If API key is invalid
            PaymentRequiredError: If account payment is required
            NetworkError: If connection issues occur
            BadRequestError: If API rejects the request
            InternalServerError: If server error occurs

        Examples:
            Standard template usage:
            ```python
            response = note_manager.process_audio(
                file_path="visit.mp3",
                visit_type="initialEncounter",
                recording_type="dictation",
                template="primaryCare"
            )
            job_id = response["job_id"]
            ```

            Word-for-word transcription:
            ```python
            response = note_manager.process_audio(
                file_path="dictation.mp3",
                lang="en",
                template="wfw"
            )
            ```

        Notes:
            The `custom` object provides powerful customization capabilities:

            * It accepts a dictionary with `context` and `template` keys (both must be strings)
            * The `template` value replaces the default note template
            * Example custom object:
            ```python
            custom = {
                "context": "Past medical history: ACL tear 10 years ago on the right knee.",
                "template": '''SOAP note template.

                SUBJECTIVE: 
                - Include the patient's subjective information here. Order by system.

                OBJECTIVE: 
                - Include the patient's objective information here.

                ASSESSMENT: 
                - Include the patient's assessment here.

                PLAN: 
                - Include the patient's plan here.'''
            }
            ```

            * You can create multiple custom templates for each template type and visit type
            * The custom object can be used in `regenerate_note()` to generate new notes from existing transcripts
            * The `context` key adds patient information not in the audio recording
            * `smartInsert` mode allows adding text snippets within a note (e.g., "Include a normal right knee exam")
        """
        # Validate input parameters
        self.logger.info("Starting audio processing for file: %s", file_path)
        self._validate_audio_file(file_path)
        self._validate_input(
            visit_type=visit_type,
            recording_type=recording_type,
            lang=lang,
            template=template,
            patient_consent=patient_consent,
            output_language=output_language,
            custom=custom
        )

        try:
            # Prepare request data
            data = {
                'lang': lang,
                'template': template,
                'file_extension': os.path.splitext(file_path)[1].lower()
            }

            # Add optional fields if provided
            if visit_type:
                data['visit_type'] = visit_type
            if recording_type:
                data['recording_type'] = recording_type
            if patient_consent is not None:
                data['patient_consent'] = patient_consent
            if output_language:
                data['output_language'] = output_language
            if custom:
                data['custom'] = custom

            # Create job and get upload URL
            self.logger.debug("Creating job with parameters: %s", data)
            response = self._request("POST", "process-audio", data=data)
            
            job_id = response.get('job_id')
            presigned_url = response.get('presigned_url')
            
            if not presigned_url or not job_id:
                raise ValidationError(
                    "Invalid API response: missing presigned_url or job_id",
                    details={"response": response}
                )

            # Upload file using presigned URL
            self.logger.info("Uploading file for job %s", job_id)
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                mime_type = VALID_AUDIO_FORMATS[file_ext]
                
                # Get file size for progress tracking
                file_size = os.path.getsize(file_path)
                uploaded = 0
                
                # Calculate optimal chunk size if not provided
                if chunk_size is None:
                    chunk_size = self._calculate_optimal_chunk_size(file_size)
                    self.logger.debug(
                        "Using adaptive chunk size of %d bytes for file size %d bytes",
                        chunk_size, file_size
                    )
                
                with open(file_path, 'rb') as f:
                    # Stream upload in chunks with progress tracking
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                            
                        uploaded += len(chunk)
                        progress = (uploaded / file_size) * 100
                        
                        self.logger.debug(
                            "Upload progress for job %s: %.1f%% (%d/%d bytes)",
                            job_id, progress, uploaded, file_size
                        )
                        
                        # Upload chunk with retries
                        retries = 0
                        while True:
                            try:
                                upload_response = requests.put(
                                    presigned_url,
                                    data=chunk,
                                    headers={'Content-Type': mime_type},
                                    timeout=self._config['request_timeout']
                                )
                                upload_response.raise_for_status()
                                break
                            except Exception as e:
                                retries += 1
                                if retries >= self._config['max_retries']:
                                    self._handle_upload_error(e, job_id)
                                delay = min(
                                    self._config['retry_delay'] * (2 ** (retries - 1)),
                                    self._config['retry_max_delay']
                                )
                                self.logger.warning(
                                    "Upload chunk failed for job %s, retrying in %d seconds (attempt %d/%d)",
                                    job_id, delay, retries, self._config['max_retries']
                                )
                                time.sleep(delay)
                
                self.logger.info("Successfully uploaded file for job %s", job_id)
                
            except Exception as e:
                self._handle_upload_error(e, job_id)

            return response

        except Exception as e:
            self.logger.error("Error in process_audio: %s", str(e))
            raise

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
        Generates a new medical note from an existing transcript with different parameters.

        This method allows you to:

        - Generate a new note using a different template
        - Translate the note to another language
        - Modify generation parameters without re-uploading audio

        Args:
            job_id (str): ID of the original job to regenerate from.
                Must be a completed job with a transcript.
            template (str, optional): New template to use for generation.
                See process_audio() for available templates.
                If not specified, uses the original template.
            output_language (str, optional): Target language for the new note:

                - 'en': English
                - 'fr': French
                If not specified, uses the original language.
            custom (dict, optional): Additional parameters for note generation:

                - context: Additional patient context (history, demographics, medication, etc.)
                - template: A complete custom template as a string (SOAP note, other etc...)

        Returns:
            dict: A dictionary containing:

                - job_id (str): New job ID for the regenerated note
                - status (str): Initial job status

        Raises:
            ValidationError: If job_id is invalid
            JobNotFoundError: If source job is not found
            JobError: If source job has no transcript or had errors
            AuthenticationError: If API key is invalid
            PaymentRequiredError: If account payment is required
            NetworkError: If connection issues occur

        Example:
            ```python
            >>> # First, get original job_id from process_audio
            >>> response = note_manager.regenerate_note(
            ...     job_id="original-job-id",
            ...     template="er",  # Change template
            ...     output_language="fr"  # Translate to French
            ... )
            >>> new_job_id = response["job_id"]
            >>> # Use new_job_id to fetch regenerated note
            ```
        """
        # Validate all inputs first
        if not job_id:
            self.logger.error("Missing required field: job_id")
            raise MissingFieldError("job_id")

        if template and template not in VALID_TEMPLATES:
            self.logger.error(
                "Invalid template value: %s. Valid values: %s",
                template, ', '.join(VALID_TEMPLATES)
            )
            raise InvalidFieldError(
                'template',
                f"Invalid value for template. Must be one of: {', '.join(VALID_TEMPLATES)}"
            )

        if output_language and output_language not in VALID_LANGUAGES:
            self.logger.error(
                "Invalid output_language: %s. Valid values: %s",
                output_language, ', '.join(VALID_LANGUAGES)
            )
            raise InvalidFieldError(
                'output_language',
                f"Invalid value for output_language. Must be one of: {', '.join(VALID_LANGUAGES)}"
            )

        # Check original job status first
        try:
            self.logger.debug("Checking status of original job %s", job_id)
            status = self.fetch_status(job_id)
            
            # Check if the original job had errors
            if status['status'] == 'error':
                error_msg = status.get('message', 'Unknown error occurred')
                self.logger.error(
                    "Cannot regenerate note from job %s - original job had errors: %s",
                    job_id, error_msg
                )
                raise JobError(
                    f"Cannot regenerate note from a failed job. Original error: {error_msg}",
                    job_id=job_id,
                    status='error',
                    details={'original_error': error_msg}
                )
            
            # Check if the job was completed
            if status['status'] != 'completed':
                self.logger.error(
                    "Cannot regenerate note from job %s - job status is %s",
                    job_id, status['status']
                )
                raise JobError(
                    f"Cannot regenerate note - job is in {status['status']} state",
                    job_id=job_id,
                    status=status['status']
                )

        except JobNotFoundError:
            self.logger.error("Original job not found: %s", job_id)
            raise
        except Exception as e:
            if not isinstance(e, JobError):  # Don't wrap JobError
                self.logger.error(
                    "Error checking original job status: %s",
                    str(e)
                )
                raise JobError(
                    f"Error checking original job status: {str(e)}",
                    job_id=job_id
                )
            raise

        # Prepare request data after all validation passes
        data = {'job_id': job_id}
        if template:
            data['template'] = template
        if output_language:
            data['output_language'] = output_language
        if custom:
            data['custom'] = custom

        try:
            self.logger.info(
                "Regenerating note from job %s with parameters: %s",
                job_id, data
            )
            
            # Make API request with retries
            response = self._request("POST", "regenerate-note", data=data)
            
            new_job_id = response.get('job_id')
            if not new_job_id:
                raise ValidationError(
                    "Invalid API response: missing job_id",
                    details={"response": response}
                )
                
            self.logger.info(
                "Successfully initiated note regeneration. New job ID: %s",
                new_job_id
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Error regenerating note from job %s: %s",
                job_id, str(e)
            )
            raise

    def fetch_status(self, job_id: str) -> Dict[str, Any]:
        """Gets the current status and progress of a note generation job.

        The job can be in one of these states:

        - 'pending': Job created, waiting for file upload
        - 'queued': File uploaded, waiting for processing
        - 'transcribing': Audio file is being transcribed
        - 'transcribed': Transcript ready, generating note
        - 'completed': Note generation finished successfully
        - 'error': Job failed with an error

        Args:
            job_id (str): The ID of the job to check.
                Obtained from process_audio() or regenerate_note().

        Returns:
            dict: A dictionary containing:

                - status (str): Current job status (see states above)
                - message (str, optional): Status message or error details
                - progress (dict, optional): Progress information

        Raises:
            ValidationError: If job_id is invalid
            JobNotFoundError: If job is not found
            AuthenticationError: If API key is invalid
            NetworkError: If connection issues occur

        Example:
            ```python
            >>> status = note_manager.fetch_status("job-id")
            >>> if status["status"] == "completed":
            ...     note = note_manager.fetch_note("job-id")
            >>> elif status["status"] == "error":
            ...     print(f"Error: {status['message']}")
            ```

        Note:
            - Poll at least 5 seconds apart if you chose this method. Webhooks are **HIGHLY** recommended.
            - The full Job typically complete within 20-30 seconds.
            - Status history is preserved for 48 hours
        """
        # Validate job_id
        if not job_id:
            self.logger.error("Missing required field: job_id")
            raise MissingFieldError("job_id")
        
        try:
            self.logger.debug("Fetching status for job %s", job_id)
            response = self._request("GET", f"status/{job_id}")
            
            # Validate response
            if 'status' not in response:
                raise ValidationError(
                    "Invalid API response: missing status field",
                    details={"response": response}
                )
                
            status = response['status']
            self.logger.info(
                "Job %s status: %s%s",
                job_id,
                status,
                f" - {response['message']}" if 'message' in response else ""
            )
            
            return response
            
        except NotFoundError:
            self.logger.error("Job not found: %s", job_id)
            raise JobNotFoundError(job_id)
            
        except Exception as e:
            self.logger.error(
                "Error fetching status for job %s: %s",
                job_id, str(e)
            )
            raise

    def fetch_note(self, job_id: str) -> Dict[str, Any]:
        """Retrieves the generated medical note for a completed job.

        The note includes:

        - Patient consent statement (if applicable)
        - Structured medical note based on template
        - Optional note title
        - Source/target language information

        Args:
            job_id (str): The ID of the job to fetch the note for.
                Job must be in 'completed' status.

        Returns:
            dict: A dictionary containing:

                - note (str): The generated medical note text
                - noteTitle (str, optional): Title for the note
                - job_id (str): The job ID (for reference)

        Raises:
            ValidationError: If job_id is invalid
            JobNotFoundError: If job or note is not found
            JobError: If note generation is not completed
            AuthenticationError: If API key is invalid
            NetworkError: If connection issues occur

        Example:
            ```python
            >>> # First check status
            >>> status = note_manager.fetch_status("job-id")
            >>> if status["status"] == "completed":
            ...     result = note_manager.fetch_note("job-id")
            ...     print(f"Title: {result['noteTitle']}")
            ...     print(f"Note: {result['note']}")
            ```

        Note:
            - Always check job status before fetching note
            - Notes are available for 48 hours after completion
            - Notes include patient consent if provided
            - The note format follows the selected template
        """
        # Validate job_id
        if not job_id:
            self.logger.error("Missing required field: job_id")
            raise MissingFieldError("job_id")
        
        try:
            self.logger.debug("Fetching note for job %s", job_id)
            response = self._request("GET", f"fetch-note/{job_id}")
            
            # Validate response
            if 'note' not in response:
                raise ValidationError(
                    "Invalid API response: missing note content",
                    details={"response": response}
                )
                
            self.logger.info(
                "Successfully retrieved note for job %s (%d characters)",
                job_id, len(response['note'])
            )
            
            return response
            
        except NotFoundError:
            self.logger.error("Job not found: %s", job_id)
            raise JobNotFoundError(job_id)
            
        except BadRequestError as e:
            if "not completed" in str(e).lower():
                self.logger.error(
                    "Note generation not completed for job %s",
                    job_id
                )
                raise JobError(
                    "Note generation not completed",
                    job_id=job_id,
                    status="incomplete",
                    details=e.details
                )
            raise
            
        except Exception as e:
            self.logger.error(
                "Error fetching note for job %s: %s",
                job_id, str(e)
            )
            raise

    def fetch_transcript(self, job_id: str) -> Dict[str, Any]:
        """Retrieves the raw transcript for a job after audio processing.

        The transcript represents the raw text from audio processing,
        before any medical note generation. Useful for:

        - Verifying audio processing accuracy
        - Debugging note generation issues
        - Keeping raw transcripts for records

        Args:
            job_id (str): The ID of the job to fetch the transcript for.
                Job must be in 'transcribed' or 'completed' status.

        Returns:
            dict: A dictionary containing:

                - transcript (str): The raw transcript text
                - job_id (str): The job ID (for reference)

        Raises:
            ValidationError: If job_id is invalid
            JobNotFoundError: If job or transcript is not found
            JobError: If transcription is not completed
            AuthenticationError: If API key is invalid
            NetworkError: If connection issues occur

        Example:
            ```python
            >>> # Useful for verification
            >>> transcript = note_manager.fetch_transcript("job-id")
            >>> print(f"Raw text: {transcript['transcript']}")
            ```

        Note:
            - Available after transcription, before note generation
            - Preserved for 48 hours after job completion
            - Includes all recognized speech from audio
            - May contain speaker labels in conversation mode
        """
        # Validate job_id
        if not job_id:
            self.logger.error("Missing required field: job_id")
            raise MissingFieldError("job_id")
        
        try:
            self.logger.debug("Fetching transcript for job %s", job_id)
            response = self._request("GET", f"fetch-transcript/{job_id}")
            
            # Validate response
            if 'transcript' not in response:
                raise ValidationError(
                    "Invalid API response: missing transcript content",
                    details={"response": response}
                )
                
            self.logger.info(
                "Successfully retrieved transcript for job %s (%d characters)",
                job_id, len(response['transcript'])
            )
            
            return response
            
        except NotFoundError:
            self.logger.error("Job not found: %s", job_id)
            raise JobNotFoundError(job_id)
            
        except BadRequestError as e:
            if "not transcribed" in str(e).lower():
                self.logger.error(
                    "Transcription not completed for job %s",
                    job_id
                )
                raise JobError(
                    "Transcription not completed",
                    job_id=job_id,
                    status="not_transcribed",
                    details=e.details
                )
            raise
            
        except Exception as e:
            self.logger.error(
                "Error fetching transcript for job %s: %s",
                job_id, str(e)
            )
            raise

    def get_system_status(self) -> Dict[str, Any]:
        """Retrieves system status and health information.

        Useful for:

        - Monitoring API availability
        - Checking processing latencies
        - Debugging connection issues

        Returns:
            dict: A dictionary containing:

                - status (str): Overall system status
                - services (dict): Status of individual services
                - latency (dict): Current processing latencies

        Raises:
            AuthenticationError: If API key is invalid
            NetworkError: If connection issues occur
            ServiceUnavailableError: If status check fails

        Example:
            ```python
            >>> status = note_manager.get_system_status()
            >>> print(f"System status: {status['status']}")
            >>> print(f"Average latency: {status['latency']['avg']}ms")
            ```

        Note:
            - Updated every minute
            - Includes all system components
            - Useful for monitoring and debugging
            - No authentication required
        """
        try:
            self.logger.debug("Fetching system status")
            response = self._request("GET", "system/status")
            
            # Validate response
            required_fields = ['status', 'services', 'latency']
            missing_fields = [field for field in required_fields 
                            if field not in response]
            
            if missing_fields:
                raise ValidationError(
                    "Invalid API response: missing required fields",
                    details={
                        "missing_fields": missing_fields,
                        "response": response
                    }
                )
                
            # Log status details
            status = response['status']
            services = response['services']
            latency = response['latency']
            
            self.logger.info(
                "System status: %s (avg latency: %dms)",
                status, latency.get('avg', 0)
            )
            
            # Log service status details at debug level
            for service, service_status in services.items():
                self.logger.debug(
                    "Service %s status: %s",
                    service, service_status
                )
            
            return response
            
        except (NoteDxError, AuthenticationError, AuthorizationError, RateLimitError):
            # Let API-specific errors propagate
            raise
            
        except Exception as e:
            self.logger.error("Error fetching system status: %s", str(e))
            raise ServiceUnavailableError(
                "System status check failed",
                details={"error": str(e)}
            )

    def _validate_audio_file(self, file_path: str) -> None:
        """Validate audio file existence, readability, and format.
        
        Performs thorough validation of the audio file:

        - Checks file existence
        - Verifies file is readable
        - Validates file format
        - Checks file size limits
        
        Args:
            file_path: Path to the audio file

        Raises:
            MissingFieldError: If file_path is empty
            ValidationError: If:

                - File doesn't exist
                - File isn't readable
                - File format is not supported
                - File size exceeds limits
        """
        if not file_path:
            self.logger.error("Missing file_path parameter")
            raise MissingFieldError("file_path")
            
        if not os.path.isfile(file_path):
            self.logger.error("Audio file not found: %s", file_path)
            raise ValidationError(
                f"Audio file not found: {file_path}",
                field="file_path",
                details={"path": file_path}
            )

        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in VALID_AUDIO_FORMATS:
            self.logger.error(
                "Unsupported audio format: %s. Supported formats: %s",
                file_ext, ', '.join(VALID_AUDIO_FORMATS.keys())
            )
            raise ValidationError(
                f"Unsupported audio format: {file_ext}. Supported formats: {', '.join(VALID_AUDIO_FORMATS.keys())}",
                field="file_path",
                details={
                    "path": file_path,
                    "extension": file_ext,
                    "supported_formats": list(VALID_AUDIO_FORMATS.keys())
                }
            )

        # Check file size (100MB limit)
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 500 * 1024 * 1024:  # 500MB
                self.logger.error(
                    "File size exceeds 500MB limit: %s (%d bytes)",
                    file_path, file_size
                )
                raise ValidationError(
                    "File size exceeds 500MB limit",
                    field="file_path",
                    details={
                        "path": file_path,
                        "size": file_size,
                        "max_size": 500 * 1024 * 1024
                    }
                )
        except OSError as e:
            self.logger.error("Cannot access file: %s", str(e))
            raise ValidationError(
                f"Cannot access file: {str(e)}",
                field="file_path",
                details={"path": file_path, "error": str(e)}
            )

        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
        except Exception as e:
            self.logger.error("Cannot read audio file: %s", str(e))
            raise ValidationError(
                f"Cannot read audio file: {str(e)}",
                field="file_path",
                details={"path": file_path, "error": str(e)}
            )

    def _handle_upload_error(self, e: Exception, job_id: str) -> None:
        """Handle file upload errors with appropriate exception types.
        
        Args:
            e: The caught exception
            job_id: ID of the job being processed
            
        Raises:
            NetworkError: For connection issues
            UploadError: For upload failures
        """
        error_msg = str(e)
        if isinstance(e, requests.RequestException):
            if isinstance(e, requests.ConnectionError):
                self.logger.error(
                    "Connection error during file upload for job %s: %s",
                    job_id, error_msg
                )
                raise NetworkError(
                    f"Connection error during file upload: {error_msg}",
                    details={"job_id": job_id}
                )
            elif isinstance(e, requests.Timeout):
                self.logger.error(
                    "Timeout during file upload for job %s: %s",
                    job_id, error_msg
                )
                raise NetworkError(
                    f"Timeout during file upload: {error_msg}",
                    details={"job_id": job_id}
                )
            
            # Handle other request exceptions
            error_msg = e.response.text if hasattr(e, 'response') else str(e)
            self.logger.error(
                "Failed to upload file for job %s: %s",
                job_id, error_msg
            )
            raise UploadError(
                f"Failed to upload file: {error_msg}",
                job_id=job_id
            )
        
        # Handle any other unexpected errors
        self.logger.error(
            "Unexpected error during upload for job %s: %s",
            job_id, error_msg
        )
        raise UploadError(
            f"Unexpected error during upload: {error_msg}",
            job_id=job_id
        ) 