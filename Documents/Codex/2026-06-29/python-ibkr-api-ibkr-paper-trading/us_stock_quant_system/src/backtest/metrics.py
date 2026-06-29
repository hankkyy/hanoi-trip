from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    return float(drawdown.min()) if not drawdown.empty else 0.0


def summarize_performance(equity_curve_df: pd.DataFrame, trades_df: pd.DataFrame, initial_equity: float) -> dict:
    equity = equity_curve_df["equity"]
    returns = equity.pct_change().dropna()
    total_return = equity.iloc[-1] / initial_equity - 1 if not equity.empty else 0
    years = max(len(equity_curve_df) / 252, 1 / 252)
    annualized_return = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1
    sharpe = float((returns.mean() / returns.std()) * math.sqrt(252)) if len(returns) > 1 and returns.std() else 0.0
    downside = returns[returns < 0]
    sortino = float((returns.mean() / downside.std()) * math.sqrt(252)) if len(downside) > 1 and downside.std() else 0.0
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] < 0]
    profit_factor = float(wins["pnl"].sum() / abs(losses["pnl"].sum())) if not losses.empty and losses["pnl"].sum() != 0 else float("inf") if not wins.empty else 0.0
    loss_streak = 0
    max_loss_streak = 0
    for pnl in trades_df["pnl"].tolist():
        if pnl < 0:
            loss_streak += 1
            max_loss_streak = max(max_loss_streak, loss_streak)
        else:
            loss_streak = 0
    return {
        "initial_equity": initial_equity,
        "final_equity": float(equity.iloc[-1]) if not equity.empty else initial_equity,
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "max_drawdown": calculate_drawdown(equity),
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "win_rate": float(len(wins) / len(trades_df)) if len(trades_df) else 0.0,
        "profit_factor": profit_factor,
        "average_win": float(wins["pnl"].mean()) if not wins.empty else 0.0,
        "average_loss": float(losses["pnl"].mean()) if not losses.empty else 0.0,
        "average_holding_days": float(trades_df["holding_days"].mean()) if len(trades_df) else 0.0,
        "number_of_trades": int(len(trades_df)),
        "exposure_time": float((equity_curve_df["positions"] > 0).mean()) if not equity_curve_df.empty else 0.0,
        "best_trade": float(trades_df["pnl"].max()) if len(trades_df) else 0.0,
        "worst_trade": float(trades_df["pnl"].min()) if len(trades_df) else 0.0,
        "max_consecutive_losses": max_loss_streak,
    }
