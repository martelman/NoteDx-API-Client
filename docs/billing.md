# Billing & Pricing

## Free Trial

Every new account starts with:

- **100 free jobs** with a live API key
- Unlimited jobs with sandbox API keys (for testing)
- Full access to all features during trial

## Pricing Model

After the free trial, we use a **tiered token pricing** model:

### Token Pricing Tiers

| Tier | Token Range | Price per 1,000 tokens |
|------|-------------|------------------------|
| 1 | 1 - 500,000 | $0.11 |
| 2 | 500,001 - 2,500,000 | $0.095 |
| 3 | 2,500,001 - 10,000,000 | $0.08 |
| 4 | 10,000,001 - 50,000,000 | $0.065 |
| 5 | 50,000,001+ | $0.05 |

### How Pricing Works

- Pricing is based on the total number of tokens processed
- Each tier's rate applies only to tokens within that tier's range
- Tokens are counted for both transcription and note generation
- Billing is calculated monthly based on total token usage

Example:
If you process 600,000 tokens in a month:

- First 500,000 tokens: $0.11 per 1,000 = $55
- Next 100,000 tokens: $0.095 per 1,000 = $9.50
- Total monthly cost = $64.50

## Account Status

Your account can be in one of these states:

**Trial**

   * Access to 100 free jobs
   * All features available
   * No credit card required

**Active**

   * Full access to all features
   * Valid subscription
   * Pay-as-you-go billing

**Pending Subscription**

   * Trial completed
   * Payment required to continue
   * Access to view past jobs only and sandbox keys

**Inactive**

   * Account setup incomplete
   * No access to API
   * Use reactivate account upon fee payments or contact support to reactivate

## Definitions

* **Job**: A single audio file processing operation including a note generation (or a regeneration)
* **Tokens**: Units of text processing in transcription and note generation (output only)
* **Live API Key**: Used for production, counts towards billing
* **Sandbox API Key**: Used for testing, no billing impact

## Token Usage Examples

### Short Visit Note
- Average dictation + note ≈ 900 tokens total
- Cost: 900 tokens × $0.11/1000 = $0.099

### Long Consultation
- Average dictation + note ≈ 2,100 tokens total
- Cost: 2,100 tokens × $0.11/1000 = $0.231

### Monthly Usage Example
Typical usage of power users (15 consultations/day, 5 days/week):

- 240 short visits: 216,000 tokens (900 × 240)
- 60 long consultations: 126,000 tokens (2,100 × 60)
- Total monthly tokens: 342,000 tokens
- Cost: 342,000 tokens × $0.11/1000 = $37.62/month (Tier 1)

***

### Check Your Usage & Billing

* Use the SDK: `client.usage.get()` to retrieve usage & cost breakdown
* Or call the endpoint `GET /usage` with your Bearer token or API key

**Next step:** [Account Management](reference/account.md)
