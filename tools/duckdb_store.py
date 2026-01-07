# tools/duckdb_store.py
from __future__ import annotations

from functools import lru_cache

import duckdb
import pandas as pd

from data.mock_data import ACCOUNTS, OPPORTUNITIES, SUBSCRIPTIONS, USAGE_METRICS


@lru_cache(maxsize=1)
def get_conn() -> duckdb.DuckDBPyConnection:
    """
    Creates an in-memory DuckDB connection and loads mock tables.

    We cache the connection so Streamlit reruns don't recreate tables repeatedly.
    """
    con = duckdb.connect(database=":memory:")

    # Convert Python lists of dicts -> pandas DataFrames (DuckDB-friendly)
    df_accounts = pd.DataFrame(ACCOUNTS)
    df_opps = pd.DataFrame(OPPORTUNITIES)
    df_subs = pd.DataFrame(SUBSCRIPTIONS)
    df_usage = pd.DataFrame(USAGE_METRICS)

    # Register DataFrames as DuckDB views and materialize as tables
    con.register("accounts_df", df_accounts)
    con.register("opportunities_df", df_opps)
    con.register("subscriptions_df", df_subs)
    con.register("usage_metrics_df", df_usage)

    con.execute("CREATE TABLE accounts AS SELECT * FROM accounts_df")
    con.execute("CREATE TABLE opportunities AS SELECT * FROM opportunities_df")
    con.execute("CREATE TABLE subscriptions AS SELECT * FROM subscriptions_df")
    con.execute("CREATE TABLE usage_metrics AS SELECT * FROM usage_metrics_df")

    return con
