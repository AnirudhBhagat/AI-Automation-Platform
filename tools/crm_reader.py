# tools/crm_reader.py
from __future__ import annotations

from pydantic import BaseModel, Field

from tools.duckdb_store import get_conn


class CRMAccount(BaseModel):
    account_id: str
    customer_name: str
    segment: str
    region: str


class CRMOpportunity(BaseModel):
    opportunity_id: str
    account_id: str
    stage: str
    requested_discount_pct: int = Field(ge=0, le=100)
    payment_terms: str
    owner: str


def get_account_by_customer_name(customer_name: str) -> CRMAccount | None:
    con = get_conn()
    row = con.execute(
        "SELECT * FROM accounts WHERE lower(customer_name) = lower(?) LIMIT 1",
        [customer_name],
    ).fetchone()
    if not row:
        return None
    return CRMAccount(
        account_id=row[0], customer_name=row[1], segment=row[2], region=row[3]
    )


def get_latest_opportunity_for_account(account_id: str) -> CRMOpportunity | None:
    con = get_conn()
    row = con.execute(
        "SELECT * FROM opportunities WHERE account_id = ? LIMIT 1",
        [account_id],
    ).fetchone()
    if not row:
        return None
    return CRMOpportunity(
        opportunity_id=row[0],
        account_id=row[1],
        stage=row[2],
        requested_discount_pct=row[3],
        payment_terms=row[4],
        owner=row[5],
    )
