# Webhook Management

Webhooks let you receive notifications when events occur (like job completion).

---

## Endpoints

1. **GET** `/user/webhooks`  
   **Description**: Get current webhook settings.  
   **Method**: `GET`  
   **Auth**: Bearer Token  
   **SDK**: `client.webhooks.get_webhook_settings()`

2. **POST** `/user/webhook`  
   **Description**: Update webhook URLs for dev/prod.  
   **Method**: `POST`  
   **Auth**: Bearer Token  
   **SDK**: `client.webhooks.update_webhook_settings(webhook_dev, webhook_prod)`

**Rules**:
- Production URL must be **HTTPS**.
- Development URL can be **HTTP** or **HTTPS**.
- Empty string clears the URL.
- At least one URL must be provided.

---

**Next step:** [Error Handling](error-handling.md)