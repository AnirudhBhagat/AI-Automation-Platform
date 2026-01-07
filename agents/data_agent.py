# agents/data_agent.py
from __future__ import annotations

from tools.data_query import get_usage_summary_last_3_months


def run(customer_name: str) -> dict:
    usage = get_usage_summary_last_3_months(customer_name)
    return {
        "status": "OK",
        "usage_summary": usage.model_dump() if usage else None,
    }
