from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.data.cache import load_ticker_data
from src.risk.stops import calculate_suggested_stop
from src.scanner.score import compute_market_score, score_ticker
from .metrics import summarize_performance
from .portfolio import Portfolio, Position
from .trade import Trade


def run_backtest(universe_cfg: dict, risk_cfg: dict, start: str, end: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    tickers = universe_cfg["universe"]["benchmark"] + universe_cfg["universe"]["stocks"]
    sectors = universe_cfg["sectors"]
    data = {}
    for ticker in tickers:
        df = load_ticker_data(ticker)
        df = df[(df["Date"] >= start) & (df["Date"] <= end)].reset_index(drop=True)
        df["Ticker"] = ticker
        data[ticker] = df
    all_dates = sorted(set(data["SPY"]["Date"]).intersection(*[set(df["Date"]) for df in data.values()]))
    initial_equity = float(risk_cfg["account"]["account_equity"])
    portfolio = Portfolio(cash=initial_equity)
    trades: list[Trade] = []
    equity_rows = []
    pending_entries: list[tuple[str, pd.Timestamp, float, float]] = []
    slippage = 0.001

    for idx, date in enumerate(all_dates[:-1]):
        date = pd.Timestamp(date)
        next_date = pd.Timestamp(all_dates[idx + 1])
        spy_row = data["SPY"].loc[data["SPY"]["Date"] == date].iloc[0]
        qqq_row = data["QQQ"].loc[data["QQQ"]["Date"] == date].iloc[0]
        market_score, _ = compute_market_score(spy_row, qqq_row)

        for ticker, signal_date, stop, score in list(pending_entries):
            next_rows = data[ticker].loc[data[ticker]["Date"] == next_date]
            if next_rows.empty:
                continue
            entry_open = float(next_rows.iloc[0]["Open"]) * (1 + slippage)
            risk_amount = (portfolio.cash + sum(
                p.shares * data[p.ticker].loc[data[p.ticker]["Date"] == date].iloc[0]["Close"]
                for p in portfolio.positions.values()
                if not data[p.ticker].loc[data[p.ticker]["Date"] == date].empty
            )) * float(risk_cfg["risk"]["risk_per_trade_pct"])
            stop_distance_pct = max((entry_open - stop) / entry_open, 0.03)
            position_value = min(risk_amount / stop_distance_pct, initial_equity * float(risk_cfg["risk"]["max_position_pct"]), float(risk_cfg["risk"]["max_order_value_usd"]))
            shares = position_value / entry_open
            if not risk_cfg["risk"]["allow_fractional_shares"]:
                shares = int(shares)
            if shares > 0 and portfolio.cash >= shares * entry_open and len(portfolio.positions) < int(risk_cfg["risk"]["max_positions"]):
                sector = sectors.get(ticker, "Unknown")
                if sector != "Semiconductor" or sum(1 for p in portfolio.positions.values() if p.sector == "Semiconductor") < int(risk_cfg["risk"]["semiconductor_max_positions"]):
                    portfolio.positions[ticker] = Position(ticker, next_date.strftime("%Y-%m-%d"), entry_open, shares, stop, sector, entry_open - stop)
                    portfolio.cash -= shares * entry_open
            pending_entries.remove((ticker, signal_date, stop, score))

        for ticker, position in list(portfolio.positions.items()):
            row = data[ticker].loc[data[ticker]["Date"] == date].iloc[0]
            exit_reason = None
            if row["Close"] < row["SMA50"]:
                exit_reason = "close_below_sma50"
            elif row["Close"] < row["Ichimoku Cloud Top"]:
                exit_reason = "fell_into_cloud"
            elif row["RSI14"] < 40 and row["MACD Histogram"] < 0:
                exit_reason = "momentum_broken"
            elif row["Close"] <= position.stop:
                exit_reason = "stop_hit"
            if exit_reason:
                exit_rows = data[ticker].loc[data[ticker]["Date"] == next_date]
                if not exit_rows.empty:
                    exit_price = float(exit_rows.iloc[0]["Open"]) * (1 - slippage)
                    pnl = (exit_price - position.entry_price) * position.shares
                    portfolio.cash += exit_price * position.shares
                    trades.append(Trade(
                        ticker=ticker,
                        entry_date=position.entry_date,
                        exit_date=next_date.strftime("%Y-%m-%d"),
                        entry_price=position.entry_price,
                        exit_price=exit_price,
                        shares=position.shares,
                        pnl=pnl,
                        holding_days=(next_date - pd.Timestamp(position.entry_date)).days,
                    ))
                    del portfolio.positions[ticker]

        candidates = []
        for ticker in universe_cfg["universe"]["stocks"]:
            row_df = data[ticker].loc[data[ticker]["Date"] == date]
            if row_df.empty or ticker in portfolio.positions:
                continue
            row = row_df.iloc[0].copy()
            row["_hist_prev1"] = data[ticker].loc[data[ticker]["Date"] <= date, "MACD Histogram"].iloc[-2] if len(data[ticker].loc[data[ticker]["Date"] <= date]) > 1 else pd.NA
            row["_hist_prev2"] = data[ticker].loc[data[ticker]["Date"] <= date, "MACD Histogram"].iloc[-3] if len(data[ticker].loc[data[ticker]["Date"] <= date]) > 2 else pd.NA
            row["Ticker"] = ticker
            scored = score_ticker(row, qqq_row, market_score)
            if scored["action"] == "BUY_CANDIDATE" and market_score >= 15:
                candidates.append((ticker, scored["score"], scored["suggested_stop"]))
        candidates.sort(key=lambda item: item[1], reverse=True)
        available_slots = int(risk_cfg["risk"]["max_positions"]) - len(portfolio.positions)
        for ticker, score, stop in candidates[: max(0, available_slots)]:
            pending_entries.append((ticker, date, stop, score))

        mtm_value = portfolio.cash
        for position in portfolio.positions.values():
            row = data[position.ticker].loc[data[position.ticker]["Date"] == date]
            if not row.empty:
                mtm_value += float(row.iloc[0]["Close"]) * position.shares
        equity_rows.append({"date": date.strftime("%Y-%m-%d"), "equity": mtm_value, "positions": len(portfolio.positions)})

    equity_curve_df = pd.DataFrame(equity_rows)
    trades_df = pd.DataFrame([trade.__dict__ for trade in trades])
    metrics = summarize_performance(equity_curve_df, trades_df if not trades_df.empty else pd.DataFrame(columns=["pnl", "holding_days"]), initial_equity)
    return metrics, trades_df, equity_curve_df
