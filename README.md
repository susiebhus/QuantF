# QuantF

QuantF is a lightweight long-term US equity monitoring system for index ETFs and large technology stocks. It is designed for a personal buy-and-hold workflow: keep watching core assets, detect long-term trend/risk changes, track portfolio concentration, and surface alerts that deserve manual review.

This project is for research and personal monitoring only. It is not investment advice.

## What This Project Does

The current MVP focuses on:

- Daily price collection
- Long-term trend indicators
- Drawdown and volatility monitoring
- Rule-based alerts
- A Streamlit dashboard

The default watchlist tracks:

```text
SPY, QQQ, VTI, NVDA, AAPL, AMZN, MSFT, SMH, XLK, SGOV
```

## Implementation Principle

QuantF follows a simple data pipeline:

```text
configs/watchlist.yaml
  -> yfinance historical daily prices
  -> DuckDB local database
  -> trend/risk indicator calculation
  -> rule-based alert engine
  -> Streamlit dashboard
```

The system is intentionally not built as a high-frequency trading bot. The first version is a long-term monitoring and decision-support tool.

## APIs And Data Sources

### Current MVP

| Data | Source | Code | Notes |
| --- | --- | --- | --- |
| Daily OHLCV prices | `yfinance` | `src/quantf/data/prices.py` | Downloads 10 years of daily market data by default |
| Watchlist symbols | Local YAML | `configs/watchlist.yaml` | Defines ETFs and stocks to monitor |
| Portfolio positions | Local YAML | `configs/portfolio.example.yaml` | Manual position input for local tracking |
| Local storage | DuckDB | `src/quantf/db/schema.py` | Stores prices, signals, and alerts |

`yfinance` is convenient for research and MVP development. For production or trading use, replace or cross-check it with a more robust data provider such as Alpaca, Polygon, Nasdaq Data Link, or Interactive Brokers.

### Planned Later

| Data | Possible Source | Purpose |
| --- | --- | --- |
| SEC filings and fundamentals | SEC EDGAR API | Revenue, EPS, cash flow, margin, financial deterioration alerts |
| Real brokerage positions | Alpaca / Interactive Brokers | Read-only account sync, then order drafts |
| Macro indicators | FRED / market data APIs | VIX, rates, inflation, liquidity context |
| News/events | SEC 8-K / earnings calendar APIs | Earnings and major event reminders |

## How Data Is Collected

The `quantf run-daily` command performs the full MVP workflow:

```text
1. Read symbols from configs/watchlist.yaml
2. Call yfinance.download(...)
3. Normalize prices into symbol/date/open/high/low/close/adj_close/volume
4. Save rows into data/quantf.duckdb -> daily_prices
5. Recompute indicators for all stored prices
6. Save calculated signals into signals_daily
7. Generate alerts from the latest signal row of each symbol
8. Save alerts into alerts
```

The default download settings are:

```python
yf.download(
    symbols,
    period="10y",
    auto_adjust=False,
    group_by="ticker",
    progress=False,
    threads=True,
)
```

## Analysis And "Prediction"

The current system does not predict tomorrow's stock price. It performs long-term state classification.

For a long-term holding system, the first useful "prediction" is not a price target. It is a structured answer to questions like:

- Is this asset still in a long-term uptrend?
- Has this asset entered a meaningful drawdown?
- Is volatility rising?
- Is the portfolio too concentrated?
- Which symbols need manual review?

### Current Algorithms

The MVP computes these indicators in `src/quantf/indicators/trend.py`:

| Indicator | Formula / Meaning |
| --- | --- |
| `ma_50` | 50-trading-day moving average |
| `ma_200` | 200-trading-day moving average |
| `return_20d` | 20-trading-day percentage return |
| `return_60d` | 60-trading-day percentage return |
| `return_252d` | 252-trading-day percentage return |
| `volatility_20d` | Annualized volatility from 20-day daily returns |
| `volatility_60d` | Annualized volatility from 60-day daily returns |
| `drawdown_from_52w_high` | Current price divided by 252-day high minus 1 |
| `drawdown_from_all_time_high` | Current price divided by historical high minus 1 |

### Trend State

```text
uptrend:
  close > ma_200 and ma_50 > ma_200

downtrend:
  close < ma_200 and ma_50 < ma_200

neutral:
  all other valid states

insufficient_data:
  not enough history to calculate MA50/MA200
```

### Risk State

```text
warning:
  drawdown_from_52w_high <= -30%

watch:
  drawdown_from_52w_high <= -20%
  or close < ma_200

normal:
  no risk rule triggered
```

### Alert Rules

The MVP alert engine lives in `src/quantf/alerts/rules.py`.

It creates alerts when:

- `trend_state == "downtrend"`: long-term trend is weak
- `risk_state == "watch"`: asset needs attention
- `risk_state == "warning"`: drawdown warning

Alerts are stored in the local `alerts` table with:

```text
id, created_at, symbol, alert_type, severity, title, message, resolved
```

## Output Results

### Command Line Output

Running:

```bash
quantf run-daily
```

prints a summary like:

```text
Daily run complete: 2510 prices, 2510 signals, 3 alerts.
```

### Database Output

The local DuckDB file stores:

| Table | Description |
| --- | --- |
| `daily_prices` | Raw normalized daily OHLCV data |
| `signals_daily` | Calculated indicators and trend/risk states |
| `alerts` | Open and historical alerts |

### Dashboard Output

Running the Streamlit app shows:

- Latest asset state table
- Close price chart by symbol
- Trend state and risk state
- 52-week drawdown
- 20-day volatility
- 60-day and 252-day returns
- Portfolio holdings from local config
- Target allocation drift
- Open alerts

## Current Limitations

The MVP does not yet include:

- SEC fundamental data
- Earnings calendar
- News analysis
- Machine learning forecasts
- Backtesting engine
- Broker account sync
- Automatic trading

These are intentionally deferred. The first milestone is to build a reliable long-term monitoring loop.

## Planned Prediction Upgrades

Future prediction/decision modules can be added in layers:

| Layer | Method | Output |
| --- | --- | --- |
| Fundamental trend | SEC revenue/EPS/cash-flow growth | `fundamental_state` |
| Valuation regime | PE/PS/FCF yield percentile | `valuation_state` |
| Market regime | SPY/QQQ trend + VIX + rates | `market_regime` |
| Portfolio risk | concentration, beta, drawdown | `portfolio_risk_state` |
| ML scoring | logistic regression / gradient boosting | probability of outperforming benchmark |

The recommended next algorithmic step is not deep learning. It is adding fundamentals and portfolio-level risk rules.

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

## Useful Commands

```bash
quantf init-db
quantf update-prices
quantf compute-signals
quantf generate-alerts
quantf run-daily
```

## Project Structure

```text
configs/
  watchlist.yaml              # Symbols to monitor
  portfolio.example.yaml      # Manual portfolio input
  alerts.yaml                 # Alert thresholds for later expansion
src/quantf/
  data/prices.py              # yfinance price download and normalization
  db/schema.py                # DuckDB tables
  indicators/trend.py         # Trend, return, volatility, drawdown indicators
  alerts/rules.py             # Rule-based alert generation
  portfolio/                  # Holdings and target allocation helpers
  app/streamlit_app.py        # Dashboard
  cli.py                      # Command-line workflow
tests/
  test_indicators.py
  test_alerts.py
```
