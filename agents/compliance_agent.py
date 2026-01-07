# agents/compliance_agent.py
from __future__ import annotations

from tools.policy_validator import validate_deal_policy


def run(discount_pct: int, computed_arr_usd: int) -> dict:
    policy = validate_deal_policy(discount_pct=discount_pct, computed_arr_usd=computed_arr_usd)
    return {"status": "OK", "policy": policy.model_dump()}
