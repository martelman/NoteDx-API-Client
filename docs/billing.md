# Billing & Pricing

We have a **tiered pricing** model:

1. **First 100 jobs** (using a live API key) are **free** for each user (across all their keys).
2. After the first 100 jobs:
   * **$0.03 per 1,000 tokens** transcribed (speech-to-text).
   * **$0.02 per 1,000 tokens** generated (NLP note generation).
3. **Discount Tiers** based on total jobs used (across all time):
   * **< 1000 jobs**: no discount
   * **1000–2999 jobs**: 7% discount
   * **3000–4999 jobs**: 12% discount
   * **5000+ jobs**: 15% discount

## Definitions

* **Job**: A single audio file processing operation (or a regeneration).
* **Tokens**: The token count in the transcription and the note.

Your usage is tracked automatically, and the discount applies to your usage cost for tokens after you reach each tier.

***

### Example Calculation

* Suppose you have done 1,200 total jobs so far.
* You are in the **7% discount** bracket.
* If you process a new note with 3,000 tokens transcribed and 2,000 tokens generated:
  * Base cost for transcription = 3,000 tokens \* $0.03/1,000 = $0.09
  * Base cost for generation = 2,000 tokens \* $0.02/1,000 = $0.04
  * Subtotal = $0.13
  * **7% discount** applies → $0.13 \* 0.93 = $0.1209 → $0.12

***

### Check Your Usage & Billing

* Use the SDK: `client.usage.get()` to retrieve usage & cost breakdown.
* Or call the endpoint `GET /usage` with your Bearer token or API key.

**Next step:** [Account Management](reference/account.md)
