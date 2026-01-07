# tools/policy_validator.py
from __future__ import annotations

from pydantic import BaseModel, Field


class PolicyResult(BaseModel):
    policy_version: str = "v1"
    discount_cap_pct: int = 20
    max_auto_approve_arr_usd: int = 200_000
    requires_director_approval: bool
    violations: list[str] = Field(default_factory=list)


def validate_deal_policy(discount_pct: int, computed_arr_usd: int) -> PolicyResult:
    violations: list[str] = []

    if discount_pct > 20:
        violations.append("DISCOUNT_EXCEEDS_CAP")

    requires = computed_arr_usd >= 200_000 or len(violations) > 0

    return PolicyResult(
        requires_director_approval=requires,
        violations=violations,
    )
