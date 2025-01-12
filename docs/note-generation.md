# Note Generation

The **NoteDx** note generation pipeline processes audio files, transcribes them, and creates structured medical notes.  

You can:
1. **Process Audio** for a new job.
2. **Regenerate Note** from an existing transcript.
3. **Fetch Status** or **Fetch Note** after completion.
4. **Fetch Transcript** if you need raw text.

**API Key** or **Bearer token** can be used, but for note generation, we typically recommend an **API Key**.

---

## 1. Process Audio

- **Endpoint**: `POST /process-audio`  
- **SDK**: `client.scribe.process_audio(...)`  
- **Auth**: `x-api-key: <YOUR_API_KEY>` or `Bearer <token>`

**Required**:
- `file_path` (.mp3)
- `visit_type` (for standard templates)
- `recording_type` (for standard templates)
- `patient_consent` (if conversation mode)
- `lang`
- `template`

**Special Templates**:
- `wfw` (word for word)
- `smartInsert`

When using these special templates, `visit_type` and `recording_type` are ignored, and `patient_consent` is not required.

Flow:
1. Request a presigned URL & job ID.
2. Upload the file.
3. The job transitions through statuses (`queued`, `transcribing`, `completed`, etc.).
4. You can select the `output_language` to be different from the `lang`.
5. You can pass a `custom` object to the template to customize the note. This is optional.

Example:

    response = client.scribe.process_audio(
        file_path="visit.mp3",
        visit_type="initialEncounter",
        recording_type="conversation",
        patient_consent=True,
        lang="en",
        template="primaryCare",
        custom={
            "template": "A complete note template with all the sections and custom format of your choice.",
            "context": "This is additionnal context about the patient you can include (e.g. age, gender, medical history, past medical history, etc. It will be passed to the model in the prompt.)"
            }
    )
    job_id = response["job_id"]

---

## 2. Regenerate Note

- **Endpoint**: `POST /regenerate-note`  
- **SDK**: `client.scribe.regenerate_note(job_id, template="er", output_language="fr")`  
- **Auth**: `x-api-key`

Use the existing transcript to generate a new note with a different template or language, no re-upload needed.

Example:

    new_job_response = client.scribe.regenerate_note(
        job_id="existing-job-id",
        template="er",
        output_language="fr"
    )
    new_job_id = new_job_response["job_id"]

---

## 3. Fetch Status

- **Endpoint**: `GET /status/{job_id}`  
- **SDK**: `client.scribe.fetch_status(job_id)`  
- **Auth**: `x-api-key`

Possible statuses: `pending`, `transcribing`, `transcribed`, `completed`, `error`.

Example:

    status = client.scribe.fetch_status("some-job-id")
    print(status["status"])

---

## 4. Fetch Note

- **Endpoint**: `GET /fetch-note/{job_id}`  
- **SDK**: `client.scribe.fetch_note(job_id)`  
- **Auth**: `x-api-key`
- Fetches the final generated medical note (when `status == completed`).

Example:

    note_response = client.scribe.fetch_note("some-job-id")
    print(note_response["note"])

---

## 5. Fetch Transcript

- **Endpoint**: `GET /fetch-transcript/{job_id}`  
- **SDK**: `client.scribe.fetch_transcript(job_id)`  
- **Auth**: `x-api-key`
- Fetches the raw transcript text (when `status` >= `transcribed`).

---

**Next step:** [Usage & Statistics](usage-management.md)