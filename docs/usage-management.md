# Usage & Statistics

Use these endpoints or SDK methods to track usage, job counts, and cost.

***

## Usage Endpoint

* **Endpoint**: `GET /usage`
* **Method**: `GET`
* **Auth**: Bearer Token
* **Description**: Returns aggregated usage information, including job counts and token usage.

Example response:

```json
{
    "period": {
        "start_month": "2025-01",
        "end_month": "2025-01"
    },
    "totals": {
        "jobs": 108,
        "transcription_tokens": 1672,
        "note_tokens": 2905,
        "base_cost": 0.07592,
        "final_cost": 0.07592,
        "savings": 0.0,
        "effective_discount_percentage": 0.0,
        "free_jobs_left": 0
    },
    "monthly_breakdown": [
        {
            "month": "2025-01",
            "jobs": 107,
            "transcription_tokens": 1520,
            "note_tokens": 2715,
            "base_cost": 0.06756,
            "final_cost": 0.06756,
            "savings": 0.0,
            "current_tier_discount": 0.0,
            "tiers": {
                "tier1": 107,
                "tier2": 0,
                "tier3": 0,
                "tier4": 0
            }
        }
    ],
    "api_keys": {
        "some api key": {
            "jobs": 107,
            "tokens": {
                "transcription": 1520,
                "note_generation": 2715
            },
            "costs": {
                "base": 0.06756,
                "final": 0.06756,
                "savings": 0.0
            },
            "tiers": {
                "tier1": 107,
                "tier2": 0,
                "tier3": 0,
                "tier4": 0
            }
        },
        "another api key": {
            "jobs": 1,
            "tokens": {
                "transcription": 152,
                "note_generation": 190
            },
            "costs": {
                "base": 0.00836,
                "final": 0.00836,
                "savings": 0.0
            },
            "tiers": {
                "tier1": 108,
                "tier2": 0,
                "tier3": 0,
                "tier4": 0
            }
        }
    }
}
```

***

## Python SDK

```python
usage_info = client.usage.get() #optional start_month and end_month params.
print(usage_info)
```

***

**Next step:** [Webhooks](webhook-management.md)
