# QuantF

QuantF is a lightweight long-term US equity monitoring system for index ETFs and large technology stocks.

The first MVP focuses on:

- Daily price collection
- Long-term trend indicators
- Drawdown and volatility monitoring
- Rule-based alerts
- A Streamlit dashboard

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
quantf run-daily
streamlit run src/quantf/app/streamlit_app.py
```

If your shell only has `python3`, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
quantf run-daily
streamlit run src/quantf/app/streamlit_app.py
```

## Default Watchlist

The default watchlist tracks:

```text
SPY, QQQ, VTI, NVDA, AAPL, AMZN, MSFT, SMH, XLK, SGOV
```

## Notes

This project is for research and personal monitoring only. It is not investment advice.
