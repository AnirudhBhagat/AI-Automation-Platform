# data/mock_data.py
from __future__ import annotations

ACCOUNTS = [
    {"account_id": "ACC_001", "customer_name": "Acme", "segment": "ENT", "region": "NA"},
    {"account_id": "ACC_002", "customer_name": "BetaCo", "segment": "SMB", "region": "EU"},
]

OPPORTUNITIES = [
    {
        "opportunity_id": "OPP_1001",
        "account_id": "ACC_001",
        "stage": "Negotiation",
        "requested_discount_pct": 15,
        "payment_terms": "NET_30",
        "owner": "sales.rep@company.com",
    },
]

SUBSCRIPTIONS = [
    {"customer_name": "Acme", "mrr_usd": 8000, "status": "active", "on_time_payment_rate": 0.96},
    {"customer_name": "BetaCo", "mrr_usd": 1200, "status": "active", "on_time_payment_rate": 0.89},
]

USAGE_METRICS = [
    {"customer_name": "Acme", "month": "2025-10", "active_seats": 220, "weekly_active_ratio": 0.72},
    {"customer_name": "Acme", "month": "2025-11", "active_seats": 235, "weekly_active_ratio": 0.74},
    {"customer_name": "Acme", "month": "2025-12", "active_seats": 240, "weekly_active_ratio": 0.76},
]
