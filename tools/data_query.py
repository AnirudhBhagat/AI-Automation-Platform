# tools/data_query.py
from __future__ import annotations

from pydantic import BaseModel, Field

from tools.duckdb_store import get_conn


class UsageSummary(BaseModel):
    customer_name: str
    avg_active_seats_3mo: float = Field(ge=0)
    avg_weekly_active_ratio_3mo: float = Field(ge=0.0, le=1.0)


def get_usage_summary_last_3_months(customer_name: str) -> UsageSummary | None:
    con = get_conn()
    row = con.execute(
        """
        SELECT
          customer_name,
          avg(active_seats) as avg_active_seats_3mo,
          avg(weekly_active_ratio) as avg_weekly_active_ratio_3mo
        FROM usage_metrics
        WHERE lower(customer_name) = lower(?)
        GROUP BY customer_name
        """,
        [customer_name],
    ).fetchone()

    if not row:
        return None

    return UsageSummary(
        customer_name=row[0],
        avg_active_seats_3mo=float(row[1]),
        avg_weekly_active_ratio_3mo=float(row[2]),
    )
