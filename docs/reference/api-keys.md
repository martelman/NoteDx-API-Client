# API Key Management

The `KeyManager` class handles all operations related to API key creation and management.

## Key Manager Class

::: notedx_sdk.api_keys.key_manager.KeyManager
    options:
      show_root_heading: true
      show_source: false

## Authentication

!!! note
    All API key management operations require Firebase authentication (email/password).
    API key authentication is not supported for these endpoints.

## Key Types

The SDK supports two types of API keys:

- `sandbox`: For testing and development
  - Limited rate limits
  - No billing
  - One per account
- `live`: For production use
  - Higher rate limits
  - Production billing
  - Multiple keys allowed

## Usage Examples

### List API Keys

```python
# Initialize with Firebase auth
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)

# List all keys (masked by default)
keys = client.keys.list_api_keys()
for key in keys:
    print(f"Key: {key['key']}")
    print(f"Type: {key['type']}")
    print(f"Status: {key['status']}")

# List with full (unmasked) keys
full_keys = client.keys.list_api_keys(show_full=True)
```

### Create API Keys

```python
# Create sandbox key
sandbox = client.keys.create_api_key(key_type="sandbox")
print(f"Sandbox key: {sandbox['api_key']}")

# Create live key with metadata
live = client.keys.create_api_key(
    key_type="live",
    metadata={
        "environment": "production",
        "department": "radiology",
        "purpose": "note-generation"
    }
)
print(f"Live key: {live['api_key']}")
```

### Manage API Keys

```python
# Update metadata
client.keys.update_metadata(
    api_key="live_abc123",
    metadata={"environment": "staging"}
)

# Update status (activate/deactivate)
client.keys.update_status(
    api_key="live_abc123",
    status="inactive"
)

# Delete key
client.keys.delete_api_key("live_abc123")
```

### Error Handling

```python
from notedx_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError
)

try:
    result = client.keys.create_api_key(
        key_type="invalid-type"
    )
except AuthenticationError:
    print("Firebase authentication required")
except AuthorizationError:
    print("Not authorized to manage keys")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
```

## REST API Equivalent

```bash
# List API keys
curl "https://api.notedx.io/v1/user/list-api-keys" \
     -H "Authorization: Bearer your-firebase-token"

# Create API key
curl -X POST "https://api.notedx.io/v1/user/create-api-key" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json" \
     -d '{
       "keyType": "live",
       "metadata": {
         "environment": "production"
       }
     }'

# Update metadata
curl -X POST "https://api.notedx.io/v1/user/update-api-key-metadata" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json" \
     -d '{
       "apiKey": "live_abc123",
       "metadata": {
         "environment": "staging"
       }
     }'

# Update status
curl -X POST "https://api.notedx.io/v1/user/api-keys/live_abc123/status" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "inactive"
     }'

# Delete key
curl -X POST "https://api.notedx.io/v1/user/delete-api-key" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json" \
     -d '{
       "apiKey": "live_abc123"
     }'
``` 