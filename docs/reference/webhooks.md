# Webhook Management

The `WebhookManager` class handles all operations related to webhook configuration and management.

## Webhook Manager Class

::: notedx_sdk.webhooks.webhook_manager.WebhookManager
    options:
      show_root_heading: true
      show_source: false

## Authentication

!!! note
    All webhook management operations require Firebase authentication (email/password).
    API key authentication is not supported for these endpoints.

## Webhook Events

Webhooks can notify you about various events:

- Note generation completion
- Processing errors
- Account status changes
- Billing events

## Environment Support

The SDK supports separate webhook URLs for:

- Development environment (`webhook_dev`)
  - Can use HTTP or HTTPS
  - Ideal for local testing
- Production environment (`webhook_prod`)
  - Must use HTTPS
  - For live deployments

## Usage Examples

### Get Webhook Settings

```python
# Initialize with Firebase auth
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)

# Get current webhook configuration
settings = client.webhooks.get_webhook_settings()
print(f"Dev webhook: {settings['webhook_dev']}")
print(f"Prod webhook: {settings['webhook_prod']}")
```

### Update Webhook URLs

```python
# Update both webhooks
result = client.webhooks.update_webhook_settings(
    webhook_dev="http://localhost:3000/webhook",
    webhook_prod="https://api.example.com/webhook"
)

# Update only development webhook
result = client.webhooks.update_webhook_settings(
    webhook_dev="http://dev.example.com/webhook"
)

# Remove development webhook
result = client.webhooks.update_webhook_settings(
    webhook_dev=""
)
```

### Error Handling

```python
from notedx_sdk.exceptions import (
    AuthenticationError,
    ValidationError
)

try:
    result = client.webhooks.update_webhook_settings(
        webhook_prod="http://insecure-url.com/webhook"  # Not HTTPS
    )
except AuthenticationError:
    print("Firebase authentication required")
except ValidationError as e:
    print(f"Invalid webhook URL: {e}")
```

## Webhook Payload Example

```json
{
  "event": "note.completed",
  "job_id": "job_abc123",
  "timestamp": "2024-01-23T12:34:56Z",
  "data": {
    "status": "completed",
    "note_id": "note_xyz789"
  }
}
```

## REST API Equivalent

```bash
# Get webhook settings
curl "https://api.notedx.io/v1/user/webhook" \
     -H "Authorization: Bearer your-firebase-token"

# Update webhook URLs
curl -X POST "https://api.notedx.io/v1/user/webhook" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json" \
     -d '{
       "webhook_dev": "http://localhost:3000/webhook",
       "webhook_prod": "https://api.example.com/webhook"
     }'
``` 