# FAQ & Troubleshooting

1. **Why am I getting a 401 "Invalid API Key"?**  
   - Verify your header: `x-api-key: <YOUR_API_KEY>`.
   - Make sure the key is **active**.

2. **Why am I getting "Account is inactive" or "Payment required"?**  
   - Your account might be cancelled or suspended due to billing.
   - Use `POST /user/reactivate-account` or contact support.

3. **My audio is large (>100MB). Any issues?**  
   - Our presigned URLs support large uploads (500MB). However, it may take longer. Ensure a stable connection.

4. **Error "Patient consent is required for conversation mode"**  
   - When `recordingType` is `"conversation"`, you **must** include `"patient_consent": "true"`.

5. **Who can I contact for support?**  
   - Email: `team@notedxai.com`
---

**End of Documentation**  
Thank you for using **NoteDx API**!