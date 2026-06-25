from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from quantf.config import DEFAULT_DB_PATH
from quantf.data.pipeline import load_ingestion_runs, load_ingestion_summary
from quantf.data.prices import load_prices
from quantf.data.quality import load_quality_summary, load_recent_quality_report
from quantf.db.connection import connect
from quantf.db.schema import ensure_schema
from quantf.events.engine import load_events
from quantf.indicators.trend import load_latest_signals
from quantf.market.regime import compute_market_regime
from quantf.portfolio.service import load_latest_portfolio_stats


st.set_page_config(page_title="QuantF", layout="wide")

conn = connect(DEFAULT_DB_PATH)
ensure_schema(conn)

latest = load_latest_signals(conn)
events = load_events(conn)
prices = load_prices(conn)
ingestion_summary = load_ingestion_summary(conn)

st.title("QuantF")
st.caption("Long-term US equity monitoring dashboard")

if latest.empty:
    st.info("No data yet. Run `quantf run-daily` first.")
    st.stop()

portfolio_stats = load_latest_portfolio_stats(conn)
market_regime = compute_market_regime(latest)

col1, col2, col3 = st.columns(3)
portfolio_value = 0 if portfolio_stats.empty else portfolio_stats["market_value"].sum()
warning_count = len(events[events["severity"].isin(["warning", "critical"])]) if not events.empty else 0
last_update = (
    ingestion_summary["last_update_time"].iloc[0]
    if not ingestion_summary.empty and "last_update_time" in ingestion_summary
    else "N/A"
)

col1.metric("Portfolio Value", f"${portfolio_value:,.2f}")
col2.metric("Market Regime", market_regime["regime"])
col3.metric("Warnings", warning_count)
st.caption(f"Last data update: {last_update}")

tab_overview, tab_assets, tab_portfolio, tab_health, tab_events = st.tabs(
    ["Overview", "Assets", "Portfolio Overview", "Data Health", "Event Timeline"]
)

with tab_overview:
    st.subheader("Market Regime")
    st.write(f"**{market_regime['regime']}** - {market_regime['reason']}")
    st.subheader("Latest Asset State")
    display_columns = [
        "symbol",
        "date",
        "close",
        "ma_20",
        "ma_50",
        "ma_200",
        "trend_state",
        "risk_state",
        "drawdown_from_52w_high",
        "volatility_20d",
        "return_60d",
        "return_252d",
        "rs_spy",
        "rs_qqq",
    ]
    display_columns = [column for column in display_columns if column in latest.columns]
    st.dataframe(
        latest[display_columns],
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
    if portfolio_stats.empty:
        st.info("No portfolio stats yet. Run `quantf run-daily` first.")
    else:
        st.subheader("Weight Drift")
        st.dataframe(portfolio_stats, use_container_width=True, hide_index=True)
        fig = px.pie(portfolio_stats, values="market_value", names="symbol", title="Portfolio Weights")
        st.plotly_chart(fig, use_container_width=True)

with tab_health:
    st.subheader("Ingestion Summary")
    st.dataframe(ingestion_summary, use_container_width=True, hide_index=True)

    st.subheader("Recent Ingestion Runs")
    st.dataframe(load_ingestion_runs(conn), use_container_width=True, hide_index=True)

    st.subheader("Data Quality Summary")
    st.dataframe(load_quality_summary(conn), use_container_width=True, hide_index=True)

    st.subheader("Recent Data Quality Reports")
    st.dataframe(load_recent_quality_report(conn), use_container_width=True, hide_index=True)

with tab_events:
    if events.empty:
        st.success("No events yet.")
    else:
        st.dataframe(events, use_container_width=True, hide_index=True)
