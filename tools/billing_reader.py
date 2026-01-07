# tools/billing_reader.py
from __future__ import annotations

from pydantic import BaseModel, Field

from tools.duckdb_store import get_conn


class BillingProfile(BaseModel):
    customer_name: str
    mrr_usd: int = Field(ge=0)
    status: str
    on_time_payment_rate: float = Field(ge=0.0, le=1.0)


def get_billing_profile(customer_name: str) -> BillingProfile | None:
    con = get_conn()
    row = con.execute(
        "SELECT * FROM subscriptions WHERE lower(customer_name) = lower(?) LIMIT 1",
        [customer_name],
    ).fetchone()
    if not row:
        return None
    return BillingProfile(
        customer_name=row[0], mrr_usd=row[1], status=row[2], on_time_payment_rate=row[3]
    )
