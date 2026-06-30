from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.utils.dates import today_str
from src.utils.paths import REPORTS_DIR


def save_scan_reports(scan_df: pd.DataFrame, market_context: dict) -> tuple[Path, Path]:
    csv_path = REPORTS_DIR / "daily" / f"{today_str()}_scan.csv"
    md_path = REPORTS_DIR / "daily" / f"{today_str()}_scan.md"
    scan_df.to_csv(csv_path, index=False)
    buy_df = scan_df[scan_df["action"] == "BUY_CANDIDATE"]
    watch_df = scan_df[scan_df["action"] == "WATCH"]
    risk_df = scan_df[scan_df["notes"].str.contains("HIGH_VOLATILITY|TOO_EXTENDED|INSUFFICIENT_DATA", na=False)]
    lines = [
        f"# Daily Scan {today_str()}",
        "",
        f"## Market State",
        f"- market_score: {market_context['market_score']}",
        f"- notes: {', '.join(market_context['notes']) or 'None'}",
        "",
        "## BUY_CANDIDATE",
        buy_df.to_markdown(index=False) if not buy_df.empty else "None",
        "",
        "## WATCH",
        watch_df.to_markdown(index=False) if not watch_df.empty else "None",
        "",
        "## Risk Warnings",
        risk_df[["ticker", "action", "notes"]].to_markdown(index=False) if not risk_df.empty else "None",
        "",
        "## Score Notes",
    ]
    for _, row in scan_df.iterrows():
        lines.append(f"- {row['ticker']}: {row['notes']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def save_risk_report(risk_df: pd.DataFrame) -> Path:
    path = REPORTS_DIR / "orders" / f"{today_str()}_risk_check.csv"
    risk_df.to_csv(path, index=False)
    return path


def save_backtest_reports(summary: dict, trades_df: pd.DataFrame, equity_curve_df: pd.DataFrame, benchmark_summary: dict) -> tuple[Path, Path, Path]:
    summary_path = REPORTS_DIR / "backtests" / f"{today_str()}_backtest_summary.md"
    trades_path = REPORTS_DIR / "backtests" / f"{today_str()}_trades.csv"
    equity_path = REPORTS_DIR / "backtests" / f"{today_str()}_equity_curve.csv"
    trades_df.to_csv(trades_path, index=False)
    equity_curve_df.to_csv(equity_path, index=False)
    strategy_vs_qqq = summary["total_return"] - benchmark_summary["QQQ buy and hold"]
    lines = [
        f"# Backtest Summary {today_str()}",
        "",
        "## Strategy Metrics",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Benchmarks"])
    for key, value in benchmark_summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Assessment"])
    if strategy_vs_qqq < 0:
        lines.append(f"- Strategy underperformed QQQ by {strategy_vs_qqq:.2%}.")
    else:
        lines.append(f"- Strategy outperformed QQQ by {strategy_vs_qqq:.2%}.")
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path, trades_path, equity_path


def save_account_sync(account: dict, positions: list[dict], open_orders: list[dict]) -> tuple[Path, Path, Path]:
    account_path = REPORTS_DIR / "account" / f"{today_str()}_account.json"
    positions_path = REPORTS_DIR / "account" / f"{today_str()}_positions.csv"
    orders_path = REPORTS_DIR / "account" / f"{today_str()}_open_orders.csv"
    account_path.write_text(json.dumps(account, indent=2), encoding="utf-8")
    pd.DataFrame(positions).to_csv(positions_path, index=False)
    pd.DataFrame(open_orders).to_csv(orders_path, index=False)
    return account_path, positions_path, orders_path


def save_order_plan(order_plan_df: pd.DataFrame) -> tuple[Path, Path]:
    csv_path = REPORTS_DIR / "orders" / f"{today_str()}_order_plan.csv"
    md_path = REPORTS_DIR / "orders" / f"{today_str()}_order_plan.md"
    order_plan_df.to_csv(csv_path, index=False)
    md_path.write_text("# Order Plan\n\n" + (order_plan_df.to_markdown(index=False) if not order_plan_df.empty else "No orders"), encoding="utf-8")
    return csv_path, md_path
