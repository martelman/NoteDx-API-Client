# Usage & Statistics

Use these endpoints or SDK methods to track usage, job counts, and cost.

---

## Usage Endpoint

- **Endpoint**: `GET /usage`  
- **Method**: `GET`  
- **Auth**: Bearer Token 
- **Description**: Returns aggregated usage information, including job counts and token usage.

Example response:

    {
      "total_jobs": 1200,
      "transcribed_tokens": 500000,
      "generated_tokens": 300000,
      "discount_rate": 0.07,
      "current_cost": 45.67,
      "billing_period": "2025-01"
    }

---

## Python SDK

    usage_info = client.usage.get_usage()
    print(usage_info)

---

**Next step:** [Webhooks](webhook-management.md)