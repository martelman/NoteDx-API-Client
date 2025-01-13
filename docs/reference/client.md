# Client Reference

The `NoteDxClient` is the main entry point for interacting with the NoteDx API.

## Client Class

::: notedx_sdk.client.NoteDxClient
    options:
      show_root_heading: true
      show_source: false

## Authentication

The client supports two authentication methods:

### API Key Authentication

```python
client = NoteDxClient(api_key="your-api-key")
```

API keys provide access to the core features around transcription and note generation.

### Firebase Authentication

```python
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)
```

Firebase authentication provides access to account management and API key operations.

## Usage Examples

### Basic Setup

```python
from notedx_sdk import NoteDxClient

# Initialize with API key
client = NoteDxClient(api_key="your-api-key")

# Or with Firebase auth - not for production
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)

# Or both
client = NoteDxClient(
    api_key="your-api-key",
    email="user@example.com",
    password="your-password"
)
```

### Accessing Managers

The client provides access to various managers for different API functionalities:

```python
# Note generation
client.notes.process_audio(...)

# Account management
client.account.get_account()

# API key management
client.keys.list_api_keys()

# Webhook management
client.webhooks.get_webhook_settings()
```

### Error Handling

```python
from notedx_sdk.exceptions import AuthenticationError, NetworkError

try:
    client = NoteDxClient(api_key="invalid-key")
    client.notes.process_audio(...)
except AuthenticationError:
    print("Invalid API key")
except NetworkError as e:
    print(f"Connection error: {e}")
```

## REST API Equivalent

```bash
# API Key Authentication
curl -X POST "https://api.notedx.io/v1/process-audio" \
     -H "x-api-key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
        "template": "primaryCare", 
        "visit_type": "followUp", 
        "recording_type": "dictation", 
        "lang":"en"
        }'

# Firebase Authentication
curl -X POST "https://api.notedx.io/v1/user/account/info" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json"
``` 