# Account Management

Manage your account details and lifecycle. **Requires email/password authentication** (Bearer token).\
API key authentication alone **cannot** manage the account.

***

## Endpoints

1. **GET** `/user/account/info`\
   **Description**: Retrieve current account information.\
   **Method**: `GET`\
   **Auth**: Bearer Token (email/password)

SDK

```python
client.account.get_account()
```

**Response** (example):

```json
{
  "company_name": "Acme Corp",
  "contact_email": "admin@acme.com",
  "phone_number": "+1-555-1234",
  "address": "123 Main Street",
  "account_status": "active",
  "created_at": "2025-01-01T12:00:00Z"
}
```

***

2.  **POST** `/user/account/update`\
    **Description**: Update account information.\
    **Method**: `POST`\
    **Auth**: Bearer Token

    **Request Fields** (any subset):

    * `company_name`
    * `contact_email`
    * `phone_number`
    * `address`

SDK

```python
client.account.update_account(...)
```

**Response** (example):

```json
{
  "message": "Account information updated successfully",
  "updated_fields": ["company_name", "contact_email"]
}
```

***

3. **POST** `/user/cancel-account`\
   **Description**: Cancel the current account. Deactivates all live API keys and sets status to `cancelled`.\
   **Method**: `POST`\
   **Auth**: Bearer Token

SDK

```python
client.account.cancel_account()
```

**Response** (example):

```json
{
  "message": "Account cancelled successfully",
  "user_id": "abc123"
}
```

***

4. **POST** `/user/reactivate-account`\
   **Description**: Reactivate a cancelled account (sets status to `inactive`).\
   **Method**: `POST`\
   **Auth**: Bearer Token

SDK

```python
client.account.reactivate_account()
```

**Response** (example):

```json
{
  "message": "Account reactivated successfully",
  "user_id": "abc123"
}
```

***

**Next step:** [API Key Management](api-key-management.md)
