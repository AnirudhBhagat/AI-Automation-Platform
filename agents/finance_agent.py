# agents/finance_agent.py
from __future__ import annotations

from tools.billing_reader import get_billing_profile


def compute_arr(deal_amount_usd: int, term_months: int) -> int:
    # deterministic annualization
    return int(round((deal_amount_usd / max(term_months, 1)) * 12))


def run(customer_name: str, deal_amount_usd: int, term_months: int) -> dict:
    billing = get_billing_profile(customer_name)

    arr = compute_arr(deal_amount_usd, term_months)

    risk_flags = []
    if billing and billing.on_time_payment_rate < 0.90:
        risk_flags.append("PAYMENT_RISK")

    return {
        "status": "OK",
        "computed_arr_usd": arr,
        "billing_profile": billing.model_dump() if billing else None,
        "risk_flags": risk_flags,
    }
