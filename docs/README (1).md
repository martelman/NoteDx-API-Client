# Introduction

Welcome to the **NoteDx** API! Our platform offers:

* **State-of-the-art speech-to-text**
* **Fully compliant to healthcare data privacy in Canada and the US**
* **Automatic medical note generation** using advanced language models
* Fully supports **English** and **French**
* **Flexible integration** via Python SDK or raw REST API endpoints (HTTP/cURL)

This introduction covers:

* **Core Concepts**
* **System Requirements**
* **Roadmap Overview**

## Core Concepts

1. **Authentication**
   * Use Firebase-based email/password for _full account management_.
   * Use an **API key** for _note generation only_.
2. **Medical Note Generation**
   * Upload audio files  via a pre-signed URL.
   * Process notes using templates like “primaryCare”, “er”, “wfw” (word-for-word), and more.
3. **Billing & Usage**
   * Track the number of jobs (each job corresponds to a transcription & note-generation task).
   * Tiered discounts available based on total job counts.
   * See [Billing & Pricing](billing.md) for details.

## System Requirements

* **Python 3.7+** (for the SDK)
* **requests** library (automatically installed if using `pip install` from PyPI)
* **HTTPS** support to call the endpoints

## Roadmap Overview

* **Real-time streaming Transcription**
* **Expanded Language Support (** Spanish **)**
* **Additional Medical Templates (** Dental medicine **)**
* **Veterinary support** 🐕 coming up as well!
* Custom `json` note generation outputs.&#x20;



**Next step:** [Authentication](authentication.md)
