# Examples

Common use cases and examples for the NoteDx SDK.

## Note Generation

### Basic Note Generation

```python
from notedx_sdk import NoteDxClient
import time

client = NoteDxClient(api_key="your-api-key")

# Process audio file
response = client.notes.process_audio(
    file_path="recording.mp3",
    template="primaryCare",
    visit_type="initialEncounter",
    recording_type="dictation",
    lang="en"
)

# Get job ID
job_id = response["job_id"]

# Check status until complete
while True:
    status = client.notes.fetch_status(job_id)
    if status["status"] == "completed":
        note = client.notes.fetch_note(job_id)
        print(note["note"])
        break
    elif status["status"] == "error":
        print(f"Error: {status['message']}")
        break
    time.sleep(5)
```

### Word-for-Word Transcription

```python
# Simple transcription without note generation
response = client.notes.process_audio(
    file_path="dictation.mp3",
    template="wfw",
    lang="en"
)

# Get transcript when ready
job_id = response["job_id"]
status = client.notes.fetch_status(job_id)
if status["status"] == "completed":
    transcript = client.notes.fetch_transcript(job_id)
    print(transcript["transcript"])
```

### Note with Custom Template

```python
# Use custom template and context
response = client.notes.process_audio(
    file_path="visit.mp3",
    template="primaryCare",
    visit_type="followUp",
    recording_type="dictation",
    lang="en",
    custom={
        "context": {
            "patient_history": "Previous visit on 2024-01-01",
            "medications": ["Medication A", "Medication B"],
            "allergies": ["Penicillin"]
        },
        "template": """
        SUBJECTIVE:
        {subjective}

        OBJECTIVE:
        {objective}

        ASSESSMENT:
        {assessment}

        PLAN:
        {plan}
        """
    }
)
```

### Note Translation

```python
# Generate note in English
response = client.notes.process_audio(
    file_path="visit.mp3",
    template="primaryCare",
    visit_type="initialEncounter",
    recording_type="dictation",
    lang="en"
)

# Later, translate to French
translated = client.notes.regenerate_note(
    job_id=response["job_id"],
    output_language="fr"
)
```

## Account Management

### Complete Account Setup

```python
from notedx_sdk import NoteDxClient

# Initialize with Firebase auth
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)

# Update account info
client.account.update_account(
    company_name="Medical Center Inc.",
    contact_email="admin@medical.com",
    phone_number="+1234567890",
    address="123 Medical Center Dr"
)

# Create API key
key = client.keys.create_api_key(
    key_type="live",
    metadata={
        "environment": "production",
        "department": "radiology"
    }
)

# Set up webhooks
client.webhooks.update_webhook_settings(
    webhook_prod="https://api.medical.com/notedx/webhook"
)
```

### Account Lifecycle

```python
# Cancel account
client.account.cancel_account()

# Later, reactivate account
client.account.reactivate_account()

# Create new API key after reactivation
new_key = client.keys.create_api_key(key_type="live")
```

## API Key Management

### Key Rotation

```python
# List current keys
current_keys = client.keys.list_api_keys()

# Create new key
new_key = client.keys.create_api_key(
    key_type="live",
    metadata={"rotated_at": "2024-01-23"}
)

# Deactivate old keys
for key in current_keys:
    if key["type"] == "live":
        client.keys.update_status(
            api_key=key["key"],
            status="inactive"
        )
```

### Environment-Specific Keys

```python
# Development key
dev_key = client.keys.create_api_key(
    key_type="live",
    metadata={
        "environment": "development",
        "rate_limit": "low"
    }
)

# Staging key
staging_key = client.keys.create_api_key(
    key_type="live",
    metadata={
        "environment": "staging",
        "rate_limit": "medium"
    }
)

# Production key
prod_key = client.keys.create_api_key(
    key_type="live",
    metadata={
        "environment": "production",
        "rate_limit": "high"
    }
)
```

## Webhook Management

### Development Setup

```python
# Set up development webhook
client.webhooks.update_webhook_settings(
    webhook_dev="http://localhost:3000/webhook"
)

# Test with sandbox key
sandbox_key = client.keys.create_api_key(key_type="sandbox")
test_client = NoteDxClient(api_key=sandbox_key["api_key"])

# Process test audio
test_client.notes.process_audio(
    file_path="test.mp3",
    template="wfw",
    lang="en"
)
```

### Production Setup

```python
# Set up production webhook with backup
client.webhooks.update_webhook_settings(
    webhook_prod="https://api.example.com/webhook",
    webhook_dev="https://backup.example.com/webhook"
)

# Create production key
prod_key = client.keys.create_api_key(
    key_type="live",
    metadata={"webhook": "https://api.example.com/webhook"}
)
```

## Error Handling

### Comprehensive Error Handling

```python
from notedx_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NetworkError,
    JobError,
    NotFoundError,
    PaymentRequiredError
)

try:
    # Attempt operation
    response = client.notes.process_audio(...)
    
except AuthenticationError:
    # Handle authentication issues
    print("Invalid API key or token expired")
    # Refresh token or get new API key
    
except AuthorizationError:
    # Handle permission issues
    print("Not authorized for this operation")
    # Check account status and permissions
    
except ValidationError as e:
    # Handle invalid parameters
    print(f"Invalid parameters: {e}")
    # Fix parameters and retry
    
except NetworkError as e:
    # Handle connection issues
    print(f"Connection error: {e}")
    # Implement exponential backoff retry
    
except JobError as e:
    # Handle job processing errors
    print(f"Job failed: {e}")
    # Check error details and retry if appropriate
    
except NotFoundError:
    # Handle missing resources
    print("Resource not found")
    # Verify resource exists
    
except PaymentRequiredError:
    # Handle billing issues
    print("Account payment required")
    # Update billing information
    
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
    # Log error and contact support
``` 