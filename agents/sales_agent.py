# agents/sales_agent.py
from __future__ import annotations

from tools.crm_reader import get_account_by_customer_name, get_latest_opportunity_for_account


def run(customer_name: str) -> dict:
    account = get_account_by_customer_name(customer_name)
    if not account:
        return {"status": "NOT_FOUND", "error": f"No account for {customer_name}"}

    opp = get_latest_opportunity_for_account(account.account_id)

    return {
        "status": "OK",
        "account": account.model_dump(),
        "opportunity": opp.model_dump() if opp else None,
    }
