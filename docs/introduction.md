# Introduction

Welcome to the **NoteDx** API! Our platform offers:
- **State-of-the-art speech-to-text**  
- **Automatic medical note generation** using advanced language models  
- **Flexible integration** via Python SDK or raw REST API endpoints (HTTP/cURL)

This introduction covers:
- **Core Concepts**  
- **System Requirements**  
- **Roadmap Overview**

## Core Concepts

1. **Authentication**  
   - Use Firebase-based email/password for *full account management*.  
   - Use an **API key** for *note generation only*.

2. **Medical Note Generation**  
   - Upload audio files (MP3) via a presigned URL.  
   - Process notes using templates like “primaryCare”, “er”, “wfw” (word-for-word), and more.

3. **Billing & Usage**  
   - Track the number of jobs (each job corresponds to a note-generation task).  
   - Tiered discounts available based on total job counts.  
   - See [Billing & Pricing](billing.md) for details.

## System Requirements

- **Python 3.7+** (for the SDK)  
- **requests** library (automatically installed if using `pip install` from PyPI)  
- **HTTPS** support to call the endpoints

## Roadmap Overview

- **Real-time Transcription** *(Upcoming)*  
- **Expanded Language Support**  
- **Additional Medical Templates**  
- **HIPAA Compliance** enhancements  

**Next step:** [Authentication](authentication.md)