# NoteDx Python SDK - Beta Access Available!

The NoteDx Python SDK provides a simple and intuitive way to interact with the NoteDx API for medical note generation and management. Fully compliant to handling of healthcare data in the US and Canada including Quebec.

## Features

- 🔒 **Secure Authentication**: API key for usage and Firebase authentication for your account management.
- 📝 **Note Generation**: Convert audio recordings to structured medical notes
- 🔄 **Real-time Status**: Track note generation progress
- 🎯 **Template Support**: Multiple medical note templates and customization
- 🌐 **Webhook Integration**: Real-time event notifications
- 🔑 **API Key Management**: Create and manage API keys
- 👥 **Account Management**: Handle account settings and status

## Quick Start

```bash
pip install notedx-sdk
```

```python
from notedx_sdk import NoteDxClient

# Initialize with API key
client = NoteDxClient(api_key="your-api-key")

# Generate a note from audio
response = client.notes.process_audio(
    file_path="recording.mp3",
    template="primaryCare",
    visit_type="initialEncounter",
    recording_type="dictation"
)

# Get the job ID
job_id = response["job_id"]

# Check status
status = client.notes.fetch_status(job_id)
if status["status"] == "completed":
    # Get the generated note
    note = client.notes.fetch_note(job_id)
    print(note["note"])
```

## API Reference

The SDK is organized into several managers for different aspects of the API:

- [Client](reference/client.md): Main client configuration and setup
- [Note Generation](reference/notes.md): Audio processing and note generation
- [Account Management](reference/account.md): Account settings and lifecycle
- [API Key Management](reference/api-keys.md): API key operations
- [Webhook Management](reference/webhooks.md): Webhook configuration

## Need Help?

- Check out our [Getting Started](getting-started.md) guide
- See [Examples](examples.md) for common use cases
- Request Beta Access [here](https://www.notedxai.com/contact-8-1)
- Contact support at team@notedxai.com 