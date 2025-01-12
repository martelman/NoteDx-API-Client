# Error Handling

The **NoteDx** API and SDK define a comprehensive exception hierarchy.

---

## Common Error Types

1. **AuthenticationError (401)**  
   - Invalid credentials, token expired, or missing credentials.

2. **AuthorizationError (403)**  
   - Lack of permission, token revoked, or account disabled.

3. **PaymentRequiredError (402)**  
   - Billing issues or unpaid balance.

4. **InactiveAccountError (403)**  
   - Account is inactive or cancelled.

5. **BadRequestError (400)**  
   - Malformed request.

6. **ValidationError (400)**  
   - Field validation error (missing or invalid field).

7. **NotFoundError (404)**  
   - Resource not found (job, user, etc.).

8. **RateLimitError (429)**  
   - Too many requests in a given timeframe.

9. **InternalServerError (500)**  
   - Server-side error.

10. **ServiceUnavailableError (503)**  
   - The system is temporarily offline or overloaded.

---

## SDK Example

    from notedx_sdk.exceptions import (
        AuthenticationError,
        AuthorizationError,
        NetworkError,
        # etc.
    )

    try:
        account_info = client.account.get_account()
    except AuthenticationError as e:
        print(f"Auth error: {e}")
    except BadRequestError as e:
        print(f"Bad request: {e}")
    except NetworkError as e:
        print(f"Network issue: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

---

**Next step:** [SDK Reference](sdk-reference.md)