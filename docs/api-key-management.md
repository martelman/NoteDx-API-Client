# API Key Management

**API keys** allow you to generate notes without storing a user’s Bearer token. On account creation, a `sandbox` api key will be automatically generated for you.

***

## Endpoints

1. **GET** `/user/list-api-keys`\
   **Description**: List all API keys associated with the account.\
   **Method**: `GET`\
   **Auth**: Bearer Token

SDK

```python
api_keys = client.keys.list_api_keys(show_full=False)
print(api_keys)

#if show_full is set to True, the keys are shown
```

**Example response:**

```json
{
    "api_keys": [
        {
            "key": "***********************ca3b",
            "type": "sandbox",
            "status": "active",
            "created_at": "2025-01-11T19:12:14.175865+00:00",
            "last_used": "2025-01-11T20:10:45.602268+00:00",
            "metadata": {}
        },
        {
            "key": "***********************8d22",
            "type": "live",
            "status": "active",
            "created_at": "2025-01-11T20:12:01.152468+00:00",
            "last_used": "2025-01-12T05:25:00.844668+00:00",
            "metadata": {}
        },
        {
            "key": "***********************b09e",
            "type": "live",
            "status": "active",
            "created_at": "2025-01-12T05:32:17.981491+00:00",
            "last_used": "2025-01-12T05:44:36.459403+00:00",
            "metadata": {
                "test": "test"
            }
        }
    ],
    "unmasked": false
}
```

2.
3.  **POST** `/user/create-api-key`\
    **Description**: Create a new API key (`sandbox` or `live`).\
    **Method**: `POST`\
    **Auth**: Bearer Token

    **Request Fields**:

    * `key_type`: `sandbox` or `live`
    * `metadata`: optional dict (only for live keys)

SDK:

```python
client.keys.create_api_key(key_type='live', metadata={"department":"radiology"})
```

**Response** (example):

```json
{
  "api_key": "live_abc123...",
  "key_type": "live",
  "metadata": {"department": "radiology"}
}
```

***

3. **POST** `/user/update-api-key-metadata`\
   **Description**: Update metadata for a live API key.\
   **Method**: `POST`\
   **Auth**: Bearer Token

SDK

```python
client.keys.update_metadata(api_key, {"department":"oncology"})
```

***

4. **POST** `/user/api-keys/{api_key}/status`\
   **Description**: Update an API key’s status (`active` or `inactive`).\
   **Method**: `POST`\
   **Auth**: Bearer Token

SDK

```python
client.keys.update_status(api_key, 'inactive')
```

***

5. **DELETE** `/user/api-keys/{api_key}`\
   **Description**: Delete an API key permanently.\
   **Method**: `DELETE`\
   **Auth**: Bearer Token

SDK

```python
client.keys.delete_api_key(api_key)
```

***

**Next step:** [Note Generation](note-generation.md)
