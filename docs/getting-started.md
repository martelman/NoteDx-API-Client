# Getting Started

This guide will help you get started with the NoteDx Python SDK.

Base URL if using HTTP requests:
```bash
https://api.notedx.io/v1
```

## Installation

Install the SDK using pip:

```bash
pip install notedx-sdk
```

Or using Poetry:

```bash
poetry add notedx-sdk
```

## Create an Account

First, create your NoteDx account:

```python
from notedx_sdk import NoteDxClient

# Create a new account
result = NoteDxClient.create_account(
    email="user@example.com",
    password="secure-password",  # Must be at least 8 characters
    company_name="Your Company Name"
)

# Save your API keys
sandbox_key = result['sandbox_api_key']  # For testing (unlimited usage)
live_key = result['live_api_key']    # For production (includes 100 free jobs)
```

After creating your account:

1. Check your email for the verification link
2. Click the verification link to activate your account
3. You can now use either your API keys or email/password to authenticate



## Authentication

The SDK supports two authentication methods.
(But you can always use `client.set_api_key(api_key)` to set the api key for any operation)

### API Key Authentication (For note related operations)

```python
from notedx_sdk import NoteDxClient

# Use your live API key for production
client = NoteDxClient(api_key=live_key)

# Or use sandbox key for testing
client = NoteDxClient(api_key=sandbox_key)
```

### Email/Password Authentication

For account management and API key operations:
You can add the api key to the client as well.

```python
client = NoteDxClient(
    email="user@example.com",
    password="your-password",
    api_key="lk-xxxxxxxxxxxx" 
)
```

## Quick Examples

### Generate a Medical Note

```python
# Initialize client with your API key
client = NoteDxClient(api_key=live_key)

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

# Polling for job completion, but it is way better to use the webhooks!
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
# Initialize with email/password
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
# Create a new live API key
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
    AuthorizationError,
    PaymentRequiredError,
    InactiveAccountError,
    ValidationError,
    NetworkError,
    JobError
)

try:
    response = client.notes.process_audio(...)
except AuthenticationError:
    print("Invalid API key or missing user")
except PaymentRequiredError as e:
    if "Free trial jobs depleted" in str(e):
        print("Free trial (100 jobs) depleted. Please subscribe.")
    else:
        print(f"Payment required: {e}")
except InactiveAccountError:
    print("Account is inactive. Please complete setup.")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except NetworkError as e:
    print(f"Connection error: {e}")
except JobError as e:
    print(f"Job failed: {e}")
```

### Free Trial Limits

- Each account starts with 100 free jobs with a live API key
- After 100 jobs, payment is required to continue
- Sandbox API keys have unlimited usage for testing

### Account Status

Your account can be in one of these states:

- `active`: Full access to all features
- `trial`: Access to 100 free jobs
- `pending_subscription`: Payment required to activate
- `inactive`: Account setup incomplete

For billing details, see [Billing & Pricing](billing.md).

## Next Steps

- Check out the [API Reference](reference/client.md) for detailed documentation
- See [Examples](examples.md) for more use cases
- Contact support at team@notedxai.com for help 