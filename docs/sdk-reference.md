# NoteDx Python SDK Reference

This section provides an overview of the Python SDK classes and methods. For detailed docstrings, refer to the source.

***

## `NoteDxClient`

**Constructor**:

```python
def __init__(
    self,
    base_url: str,
    email: Optional[str] = None,
    password: Optional[str] = None,
    api_key: Optional[str] = None,
    auto_login: bool = True,
    session: Optional[requests.Session] = None
)
```

* `base_url`: e.g. `"https://api.notedx.io/v1"`.
* `email` + `password`: For Firebase auth.
* `api_key`: For note-generation auth.
* `auto_login`: If True, logs in automatically with email/password.
* `session`: Optional custom `requests.Session`.

### Sub-Modules

* `client.account` → `AccountManager`
  * `get_account()`, `update_account(...)`, `cancel_account()`, `reactivate_account()`
* `client.keys` → `KeyManager`
  * `list_api_keys()`, `create_api_key(...)`, `update_metadata(...)`, `update_status(...)`, `delete_api_key(...)`
* `client.scribe` → `NoteManager` (Note Generation)
  * `process_audio(...)`, `regenerate_note(...)`, `fetch_status(...)`, `fetch_note(...)`, `fetch_transcript(...)`
* `client.webhooks` → `WebhookManager`
  * `get_webhook_settings()`, `update_webhook_settings(...)`
* `client.usage` → `UsageManager`
  * `get_usage()`

***

## Example Usage

```python
# Initialize with email/password (Full Account Access)
client = NoteDxClient(
    base_url="https://api.notedx.io/v1",
    email="user@example.com",
    password="secret",
    auto_login=True
)

# Fetch account details
acct = client.account.get_account()

# Switch to an API key for note generation
client.set_api_key("YOUR_API_KEY")
res = client.scribe.process_audio(
    file_path="visit.mp3",
    visit_type="initialEncounter",
    recording_type="conversation",
    patient_consent=True,
    lang="en",
    template="primaryCare"
)
job_id = res["job_id"]
```

***

**Next step:** [cURL & HTTP Examples](curl-examples.md)
