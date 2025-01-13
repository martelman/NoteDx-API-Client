# Account Management

The `AccountManager` class handles all operations related to account management and settings.

## Account Manager Class

::: notedx_sdk.account.account_manager.AccountManager
    options:
      show_root_heading: true
      show_source: false

## Authentication

!!! note
    All account management operations require Firebase authentication (email/password).
    API key authentication is not supported for these endpoints.

## Usage Examples

### Get Account Information

```python
# Initialize with Firebase auth
client = NoteDxClient(
    email="user@example.com",
    password="your-password"
)

# Get account info
account_info = client.account.get_account()
print(f"Company: {account_info['company_name']}")
print(f"Status: {account_info['account_status']}")
```

### Update Account Settings

```python
# Update account information
result = client.account.update_account(
    company_name="New Company Name",
    contact_email="new@example.com",
    phone_number="+1234567890",
    address="123 Medical Center Dr"
)
```

### Account Lifecycle Management

```python
# Cancel account
result = client.account.cancel_account()
print(f"Account {result['user_id']} cancelled")

# Later, reactivate account
result = client.account.reactivate_account()
print(f"Account {result['user_id']} reactivated")
```

### Error Handling

```python
from notedx_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidFieldError
)

try:
    result = client.account.update_account(
        contact_email="invalid-email"
    )
except AuthenticationError:
    print("Firebase authentication required")
except AuthorizationError:
    print("Not authorized to update account")
except InvalidFieldError as e:
    print(f"Invalid field value: {e}")
```

## REST API Equivalent

```bash
# Get account info
curl "https://api.notedx.io/v1/user/account/info" \
     -H "Authorization: Bearer your-firebase-token"

# Update account
curl -X POST "https://api.notedx.io/v1/user/account/update" \
     -H "Authorization: Bearer your-firebase-token" \
     -H "Content-Type: application/json" \
     -d '{
       "company_name": "New Company Name",
       "contact_email": "new@example.com"
     }'

# Cancel account
curl -X POST "https://api.notedx.io/v1/user/cancel-account" \
     -H "Authorization: Bearer your-firebase-token"

# Reactivate account
curl -X POST "https://api.notedx.io/v1/user/reactivate-account" \
     -H "Authorization: Bearer your-firebase-token"
``` 