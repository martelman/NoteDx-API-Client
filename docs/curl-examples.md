# cURL & HTTP Examples

Here are quick cURL snippets for each major endpoint. Replace `https://api.notedx.io/v1` with your actual base URL if needed.

---

## 1. Authentication
```bash
    # Login with email/password
    curl -X POST "https://api.notedx.io/v1/auth/login" \
         -H "Content-Type: application/json" \
         -d '{
               "email": "someone@example.com",
               "password": "secretpassword"
             }'
```

---

## 2. Account Management
```bash
    # Get Account Info
    curl -X GET "https://api.notedx.io/v1/user/account/info" \
         -H "Authorization: Bearer <your_id_token>"
```

```bash
    # Update Account
    curl -X POST "https://api.notedx.io/v1/user/account/update" \
         -H "Authorization: Bearer <your_id_token>" \
         -H "Content-Type: application/json" \
         -d '{
               "company_name": "New Company",
               "address": "456 Maple Ave"
             }'
```

---

## 3. API Keys
```bash
    # List API Keys
    curl -X GET "https://api.notedx.io/v1/user/list-api-keys" \
         -H "Authorization: Bearer <your_id_token>"
```

```bash
    # Create API Key (live)
    curl -X POST "https://api.notedx.io/v1/user/create-api-key" \
         -H "Authorization: Bearer <your_id_token>" \
         -H "Content-Type: application/json" \
         -d '{
               "key_type": "live",
               "metadata": { "department": "cardiology" }
             }'

```

---

## 4. Note Generation
```bash
    # Process Audio (with x-api-key)
    curl -X POST "https://api.notedx.io/v1/process-audio" \
         -H "Content-Type: application/json" \
         -H "x-api-key: YOUR_API_KEY" \
         -d '{
               "visit_type": "initialEncounter",
               "recording_type": "dictation",
               "consent": "true",
               "lang": "en",
               "template": "primaryCare"
             }'
```

```bash
    # Response includes "job_id" and "presigned_url"
    # Then upload the file:
    curl -X PUT "<presigned_url>" \
         -H "Content-Type: audio/mpeg" \
         --data-binary "@visit.mp3"
```

```bash
    # Fetch Status
    curl -X GET "https://api.notedx.io/v1/status/<job_id>" \
         -H "x-api-key: YOUR_API_KEY"
```

```bash
    # Fetch Note
    curl -X GET "https://api.notedx.io/v1/fetch-note/<job_id>" \
         -H "x-api-key: YOUR_API_KEY"
```

---

## 5. Usage & Billing
```bash
    curl -X GET "https://api.notedx.io/v1/usage" \
         -H "Authorization: Bearer <your_id_token>"
```

```bash
    # or with x-api-key:
    curl -X GET "https://api.notedx.io/v1/usage" \
         -H "x-api-key: YOUR_API_KEY"
```

---

## 6. Webhooks
```bash
    # Get Webhook Settings
    curl -X GET "https://api.notedx.io/v1/user/webhooks" \
         -H "Authorization: Bearer <your_id_token>"
```

```bash
    # Update Webhook
    curl -X POST "https://api.notedx.io/v1/user/webhook" \
         -H "Authorization: Bearer <your_id_token>" \
         -H "Content-Type: application/json" \
         -d '{
               "webhookDev": "http://dev.example.com/webhook",
               "webhookProd": "https://prod.example.com/webhook"
             }'
```
