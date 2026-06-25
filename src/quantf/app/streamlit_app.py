from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from quantf.alerts.rules import load_open_alerts
from quantf.config import DEFAULT_DB_PATH
from quantf.data.prices import load_prices
from quantf.db.connection import connect
from quantf.db.schema import ensure_schema
from quantf.indicators.trend import load_latest_signals
from quantf.portfolio.allocation import compare_to_target, load_target_allocation
from quantf.portfolio.holdings import build_portfolio_snapshot, load_positions


st.set_page_config(page_title="QuantF", layout="wide")

conn = connect(DEFAULT_DB_PATH)
ensure_schema(conn)

latest = load_latest_signals(conn)
alerts = load_open_alerts(conn)
prices = load_prices(conn)

st.title("QuantF")
st.caption("Long-term US equity monitoring dashboard")

if latest.empty:
    st.info("No data yet. Run `quantf run-daily` first.")
    st.stop()

positions = load_positions()
snapshot = build_portfolio_snapshot(positions, latest)
target = load_target_allocation()
allocation = compare_to_target(snapshot, target)

col1, col2, col3 = st.columns(3)
portfolio_value = 0 if snapshot.empty else snapshot["market_value"].sum()
warning_count = len(alerts[alerts["severity"].isin(["warning", "critical"])]) if not alerts.empty else 0
watch_count = len(alerts[alerts["severity"] == "watch"]) if not alerts.empty else 0

col1.metric("Portfolio Value", f"${portfolio_value:,.2f}")
col2.metric("Warnings", warning_count)
col3.metric("Watch Alerts", watch_count)

tab_overview, tab_assets, tab_portfolio, tab_alerts = st.tabs(
    ["Overview", "Assets", "Portfolio", "Alerts"]
)

with tab_overview:
    st.subheader("Latest Asset State")
    st.dataframe(
        latest[
            [
                "symbol",
                "date",
                "close",
                "trend_state",
                "risk_state",
                "drawdown_from_52w_high",
                "volatility_20d",
                "return_60d",
                "return_252d",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tab_assets:
    symbol = st.selectbox("Symbol", sorted(latest["symbol"].unique()))
    asset_prices = prices[prices["symbol"] == symbol].sort_values("date")
    asset_signals = latest[latest["symbol"] == symbol]

    if not asset_prices.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=asset_prices["date"],
                y=asset_prices["adj_close"].fillna(asset_prices["close"]),
                name="Adjusted Close",
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(asset_signals, use_container_width=True, hide_index=True)

with tab_portfolio:
    if snapshot.empty:
        st.info("No portfolio positions configured.")
    else:
        st.subheader("Holdings")
        st.dataframe(snapshot, use_container_width=True, hide_index=True)
        fig = px.pie(snapshot, values="market_value", names="symbol", title="Portfolio Weights")
        st.plotly_chart(fig, use_container_width=True)

    if not allocation.empty:
        st.subheader("Target Allocation Drift")
        st.dataframe(allocation, use_container_width=True, hide_index=True)

with tab_alerts:
    if alerts.empty:
        st.success("No open alerts.")
    else:
        st.dataframe(alerts, use_container_width=True, hide_index=True)
