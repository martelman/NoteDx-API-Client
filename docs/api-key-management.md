# API Key Management

**API keys** allow you to generate notes without storing a user’s Bearer token.  

---

## Endpoints

1. **GET** `/user/list-api-keys`  
   **Description**: List all API keys associated with the account.  
   **Method**: `GET`  
   **Auth**: Bearer Token  
   **SDK**: `client.keys.list_api_keys(show_full=False)`

---

2. **POST** `/user/create-api-key`  
   **Description**: Create a new API key (`sandbox` or `live`).  
   **Method**: `POST`  
   **Auth**: Bearer Token  
   **SDK**: `client.keys.create_api_key(key_type='live', metadata={"department":"radiology"})`

   **Request Fields**:
   - `key_type`: `sandbox` or `live`
   - `metadata`: optional dict (only for live keys)

   **Response** (example):
    
       {
         "api_key": "live_abc123...",
         "key_type": "live",
         "metadata": {"department": "radiology"}
       }

---

3. **POST** `/user/update-api-key-metadata`  
   **Description**: Update metadata for a live API key.  
   **Method**: `POST`  
   **Auth**: Bearer Token  
   **SDK**: `client.keys.update_metadata(api_key, {"department":"oncology"})`

---

4. **POST** `/user/api-keys/{api_key}/status`  
   **Description**: Update an API key’s status (`active` or `inactive`).  
   **Method**: `POST`  
   **Auth**: Bearer Token  
   **SDK**: `client.keys.update_status(api_key, 'inactive')`

---

5. **DELETE** `/user/api-keys/{api_key}`  
   **Description**: Delete an API key permanently.  
   **Method**: `DELETE`  
   **Auth**: Bearer Token  
   **SDK**: `client.keys.delete_api_key(api_key)`

---

**Next step:** [Note Generation](note-generation.md)