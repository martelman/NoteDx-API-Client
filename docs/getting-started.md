# Getting Started

This guide will help you get started with the NoteDx Python SDK.

## Installation

Install the SDK using pip:

```bash
pip install notedx-sdk
```

Or using Poetry:

```bash
poetry add notedx-sdk
```

## Authentication

The SDK supports two authentication methods:

### API Key Authentication

For production use, authenticate with an API key:

```python
from notedx_sdk import NoteDxClient

client = NoteDxClient(api_key="your-api-key")
```

### Firebase Authentication

For account management and API key operations, use Firebase authentication:

```python
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)
```

## Quick Examples

### Generate a Medical Note

```python
# Initialize client
client = NoteDxClient(api_key="your-api-key")

# Process audio file
response = client.notes.process_audio(
    file_path="visit_recording.mp3",
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
        # Get the note
        note = client.notes.fetch_note(job_id)
        print(note["note"])
        break
    elif status["status"] == "error":
        print(f"Error: {status['message']}")
        break
    time.sleep(5)  # Wait 5 seconds before checking again
```

### Manage Account Settings

```python
# Initialize with Firebase auth
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)

# Get account info
account_info = client.account.get_account()
print(f"Company: {account_info['company_name']}")

# Update settings
client.account.update_account(
    company_name="New Company Name",
    contact_email="new@example.com"
)
```

### Manage API Keys

```python
# Create a live API key
key = client.keys.create_api_key(
    key_type="live",
    metadata={"environment": "production"}
)
print(f"New API key: {key['api_key']}")

# List all keys
keys = client.keys.list_api_keys()
for key in keys:
    print(f"Key: {key['key']}, Type: {key['type']}")
```

### Configure Webhooks

```python
# Set up webhooks for notifications
client.webhooks.update_webhook_settings(
    webhook_dev="http://localhost:3000/webhook",
    webhook_prod="https://api.example.com/webhook"
)
```

## Error Handling

The SDK provides detailed error classes for better error handling:

```python
from notedx_sdk.exceptions import (
    AuthenticationError,
    ValidationError,
    NetworkError,
    JobError
)

try:
    response = client.notes.process_audio(...)
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except NetworkError as e:
    print(f"Connection error: {e}")
except JobError as e:
    print(f"Job failed: {e}")
```

## Next Steps

- Check out the [API Reference](reference/client.md) for detailed documentation
- See [Examples](examples.md) for more use cases
- Request Beta Access [here](https://www.notedxai.com/contact-8-1)
- Contact support at team@notedxai.com for help 