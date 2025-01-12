# Authentication

The **NoteDx** platform supports two main authentication methods:

1. **Email/Password** (Firebase)  
2. **API Key** (for note generation)

---

## 1. Requesting an Account

To get started, request account creation by filling out our form:  
[Request an account creation here](https://example.com/form)

Once approved, you’ll receive:
- **Email & Password** for user-level authentication.
- (Optional) **API Key** for direct note generation.

---

## 2. Using Email/Password

**Email/Password** provides full access, allowing you to:
- Manage account & billing
- Manage API keys
- Generate medical notes

**Python SDK Example**:

    from notedx_sdk.client import NoteDxClient

    client = NoteDxClient(
        base_url="https://api.notedx.io/v1",
        email="your.email@example.com",
        password="your_password"
    )

    # This automatically logs in by default (auto_login=True).
    # You can now call any resource, e.g. get account info:
    account_info = client.account.get_account()
    print(account_info)

**HTTP/cURL Example**:

    # 1. Obtain a token using email/password
    curl -X POST "https://api.notedx.io/v1/auth/login" \
         -H "Content-Type: application/json" \
         -d '{
               "email": "your.email@example.com",
               "password": "your_password"
             }'

    # Response will include "id_token" which you need to store.
    # Then, for subsequent requests:
    curl -X GET "https://api.notedx.io/v1/user/account/info" \
         -H "Authorization: Bearer <id_token>" \
         -H "Content-Type: application/json"

---

## 3. Using API Key

**API Key** authentication is for:
- Generating notes (audio file processing)
- Access to note/transcript endpoints

**Python SDK Example**:

    from notedx_sdk.client import NoteDxClient

    client = NoteDxClient(
        base_url="https://api.notedx.io/v1",
        api_key="YOUR_API_KEY"
    )

    # Note management calls are available, e.g.:
    job_response = client.scribe.process_audio(
        file_path="recording.mp3",
        visit_type="initialEncounter",
        recording_type="conversation",
        patient_consent=True,
        lang="en",
        template="primaryCare"
    )
    print(job_response)

**HTTP/cURL Example**:

    # For note generation endpoints, pass x-api-key in the header:
    curl -X POST "https://api.notedx.io/v1/process-audio" \
         -H "Content-Type: application/json" \
         -H "x-api-key: YOUR_API_KEY" \
         -d '{
               "visitType": "initialEncounter",
               "recordingType": "conversation",
               "lang": "en",
               "consent": "true",
               "template": "primaryCare"
             }'

---

**Next step:** [Billing & Pricing](billing.md)