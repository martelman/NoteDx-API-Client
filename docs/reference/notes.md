# Note Generation

The `NoteManager` class handles all operations related to generating medical notes from audio recordings.

## Note Manager Class

::: notedx_sdk.core.note_manager.NoteManager
    options:
      show_root_heading: true
      show_source: false

## Templates

The SDK supports various medical note templates:

- `primaryCare`: Primary care visit notes
- `er`: Emergency room visit notes
- `psychiatry`: Psychiatric evaluation notes
- `surgicalSpecialties`: Surgical specialties notes
- `medicalSpecialties`: Medical specialties notes
- `nursing`: Nursing notes
- `radiology`: Radiology reports
- `procedures`: Procedure notes
- `letter`: Medical letters
- `social`: Social worker notes
- `wfw`: Word-for-word transcription
- `smartInsert`: Smart insertion mode

## Usage Examples

### Basic Note Generation

```python
# Initialize client
client = NoteDxClient(api_key="your-api-key")

# Step 1: Process audio request - get job_id and upload URL
response = client.notes.process_audio(
    template="primaryCare",
    visit_type="initialEncounter",
    recording_type="dictation",
    lang="en"
)

# Get job ID and presigned URL
job_id = response["job_id"]
presigned_url = response["presigned_url"]

# Step 2: Upload the audio file using presigned URL
client.notes.upload_audio(
    presigned_url=presigned_url,
    file_path="visit_recording.mp3"
)

# Step 3: Check status until complete
while True:
    status = client.notes.fetch_status(job_id)
    if status["status"] == "completed":
        # Step 4: Get the note
        note = client.notes.fetch_note(job_id)
        print(note["note"])
        break
    elif status["status"] == "error":
        print(f"Error: {status['message']}")
        break
    time.sleep(5)  # Wait 5 seconds before checking again
```

### Word-for-Word Transcription

```python
# Get job_id and upload URL
response = client.notes.process_audio(
    template="wfw",
    lang="en"
)

# Upload the audio file
client.notes.upload_audio(
    presigned_url=response["presigned_url"],
    file_path="dictation.mp3"
)
```

### Note Regeneration

```python
# Regenerate with different template
new_response = client.notes.regenerate_note(
    job_id="original-job-id",
    template="er"
)

# Translate to French
translated = client.notes.regenerate_note(
    job_id="original-job-id",
    output_language="fr"
)
```

### Error Handling

```python
from notedx_sdk.exceptions import ValidationError, JobError

try:
    response = client.notes.process_audio(
        file_path="recording.mp3",
        template="invalid-template"
    )
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except JobError as e:
    print(f"Job failed: {e}")
```

## REST API Equivalent

```bash
# Step 1: Initialize processing and get upload URL
curl -X POST "https://api.notedx.io/v1/process-audio" \
     -H "x-api-key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "template": "primaryCare",
       "visit_type": "initialEncounter",
       "recording_type": "dictation",
       "lang": "en"
     }'
     
# Response contains job_id and presigned_url

# Step 2: Upload audio file using presigned URL
curl -X PUT "${presigned_url}" \
     -H "Content-Type: audio/mpeg" \
     --data-binary "@recording.mp3"

# Step 3: Check processing status
curl "https://api.notedx.io/v1/status/{job_id}" \
     -H "x-api-key: your-api-key"

# Step 4: Get the generated note
curl "https://api.notedx.io/v1/fetch-note/{job_id}" \
     -H "x-api-key: your-api-key"
``` 