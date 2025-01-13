[![Tests](https://github.com/martelman/NoteDx-API-Client/actions/workflows/test.yml/badge.svg)](https://github.com/martelman/NoteDx-API-Client/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/martelman/NoteDx-API-Client/graph/badge.svg?token=O64HJ8B0BF)](https://codecov.io/gh/martelman/NoteDx-API-Client)
![PyPI](https://img.shields.io/pypi/v/notedx-sdk)
![Last Commit](https://img.shields.io/github/last-commit/martelman/NoteDx-API-Client)


# NoteDx API Python Client

Official Python SDK for the NoteDx API - a powerful medical note generation service that converts audio recordings into structured medical notes, fully compliant with data privay laws in Canada and the US.

## Features

- Audio to medical note conversion
- Support for multiple languages (English, French)
- Multiple medical note templates
- Real-time job status tracking
- Webhook integration
- Usage monitoring

## Installation

```bash
pip install notedx-sdk
```

## Quick Start

```python
from notedx_sdk import NoteDxClient

# Initialize client
client = NoteDxClient(api_key="your-api-key")

# Process audio file
response = client.notes.process_audio(
    file_path="visit.mp3",
    visit_type="initialEncounter",
    recording_type="dictation",
    patient_consent=True,
    template="primaryCare"
)

# Get job ID
job_id = response["job_id"]

# Check status
status = client.notes.fetch_status(job_id)

# Get note when ready
if status["status"] == "completed":
    note = client.notes.fetch_note(job_id)
```

## Supported Audio Formats

- MP3 (.mp3)
- MP4/M4A (.mp4, .m4a)
- AAC (.aac)
- WAV (.wav)
- FLAC (.flac)
- PCM (.pcm)
- OGG (.ogg)
- Opus (.opus)
- WebM (.webm)

## Development

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

## Documentation

For complete documentation, visit [NoteDx API Documentation](https://martelman.github.io/NoteDx-API-Client/).

## License

Copyright © 2025 Technologies Medicales JLA Shiftpal inc. All rights reserved.