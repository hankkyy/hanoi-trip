from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from src.backtest.engine import run_backtest
from src.brokers.dry_run_broker import DryRunBroker
from src.brokers.ibkr_broker import IBKRBroker
from src.brokers.order_models import OrderModel
from src.brokers.safety import BrokerSafetyError, build_broker_safety_state, validate_broker_safety_config
from src.data.cache import load_ticker_data, save_ticker_data
from src.data.mock_provider import MockProvider
from src.data.validators import validate_ohlcv
from src.data.yfinance_provider import YFinanceProvider
from src.indicators.technicals import add_indicators
from src.reporting.charts import save_equity_curve_chart
from src.reporting.report_generator import save_account_sync, save_backtest_reports, save_order_plan, save_risk_report, save_scan_reports
from src.risk.risk_rules import risk_check
from src.scanner.scanner import run_scan
from src.utils.config_loader import load_all_configs
from src.utils.dates import today_str
from src.utils.logger import setup_logger
from src.utils.paths import REPORTS_DIR, ensure_directories


console = Console()


def get_tickers(configs: dict) -> list[str]:
    universe = configs["universe"]["universe"]
    return universe["benchmark"] + universe["stocks"]


def download_data() -> None:
    configs = load_all_configs()
    data_cfg = configs["settings"]["data"]
    tickers = get_tickers(configs)
    y_provider = YFinanceProvider()
    mock_provider = MockProvider()
    summary_rows = []
    for ticker in tickers:
        source = "yfinance"
        try:
            df = y_provider.fetch_history(
                ticker=ticker,
                start_date=data_cfg["start_date"],
                end_date=data_cfg["end_date"],
                interval=data_cfg["interval"],
                auto_adjust=data_cfg["auto_adjust"],
            )
        except Exception as exc:
            if not data_cfg.get("fallback_to_mock", True):
                console.print(f"[red]{ticker} failed without fallback:[/red] {exc}")
                continue
            source = "mock"
            console.print(f"[yellow]{ticker} yfinance failed, fallback to mock:[/yellow] {exc}")
            df = mock_provider.fetch_history(
                ticker=ticker,
                start_date=data_cfg["start_date"],
                end_date=data_cfg["end_date"],
                interval=data_cfg["interval"],
                auto_adjust=data_cfg["auto_adjust"],
            )
        validation = validate_ohlcv(df)
        save_ticker_data(ticker, df)
        start_value = pd.to_datetime(df["Date"]).min().strftime("%Y-%m-%d")
        end_value = pd.to_datetime(df["Date"]).max().strftime("%Y-%m-%d")
        summary_rows.append({
            "ticker": ticker,
            "source": source,
            "start": start_value,
            "end": end_value,
            "rows": len(df),
            "validation": "PASS" if validation.passed else f"FAIL:{'|'.join(validation.issues)}",
        })
    table = Table(title="Download Data Summary")
    for column in ["ticker", "source", "start", "end", "rows", "validation"]:
        table.add_column(column)
    for row in summary_rows:
        table.add_row(*(str(row[c]) for c in ["ticker", "source", "start", "end", "rows", "validation"]))
    console.print(table)


def compute_indicators() -> None:
    configs = load_all_configs()
    rows = []
    for ticker in get_tickers(configs):
        try:
            df = load_ticker_data(ticker)
            out = add_indicators(df)
            save_ticker_data(ticker, out)
            valid_count = int(out[["SMA20", "MACD", "RSI14", "ATR14"]].dropna().shape[0])
            rows.append((ticker, "SUCCESS", str(valid_count)))
        except Exception as exc:
            rows.append((ticker, "FAILED", str(exc)))
    table = Table(title="Indicator Summary")
    for column in ["ticker", "status", "details"]:
        table.add_column(column)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def scan() -> pd.DataFrame:
    configs = load_all_configs()
    scan_df, market_context = run_scan(configs["universe"])
    save_scan_reports(scan_df, market_context)
    table = Table(title="Scan Results")
    for column in ["ticker", "score", "market_score", "action", "close", "notes"]:
        table.add_column(column)
    for _, row in scan_df.iterrows():
        table.add_row(
            row["ticker"],
            str(row["score"]),
            str(row["market_score"]),
            row["action"],
            f"{row['close']:.2f}",
            row["notes"][:80],
        )
    console.print(table)
    return scan_df


def run_risk_check() -> pd.DataFrame:
    configs = load_all_configs()
    scan_path = REPORTS_DIR / "daily" / f"{today_str()}_scan.csv"
    scan_df = pd.read_csv(scan_path) if scan_path.exists() else scan()
    risk_df = risk_check(scan_df, configs["universe"], configs["risk"])
    save_risk_report(risk_df)
    console.print(risk_df.to_string(index=False) if not risk_df.empty else "No BUY_CANDIDATE rows for risk check.")
    return risk_df


def _load_broker():
    configs = load_all_configs()
    safety_state = build_broker_safety_state(configs)
    broker_active = configs["broker"]["broker"]["active"]
    if broker_active == "dry_run":
        return DryRunBroker(safety_state), safety_state
    return IBKRBroker(safety_state), safety_state


def _load_scan_and_risk():
    scan_path = REPORTS_DIR / "daily" / f"{today_str()}_scan.csv"
    risk_path = REPORTS_DIR / "orders" / f"{today_str()}_risk_check.csv"
    scan_df = pd.read_csv(scan_path) if scan_path.exists() else scan()
    risk_df = pd.read_csv(risk_path) if risk_path.exists() else run_risk_check()
    return scan_df, risk_df


def generate_order_plan(current_positions: list[dict] | None = None) -> pd.DataFrame:
    current_positions = current_positions or []
    configs = load_all_configs()
    scan_df, risk_df = _load_scan_and_risk()
    current_position_tickers = {p.get("ticker") for p in current_positions}
    plan_rows = []
    for _, row in risk_df.iterrows():
        scan_row = scan_df.loc[scan_df["ticker"] == row["ticker"]].iloc[0]
        submit_allowed = bool(row["position_allowed"])
        block_reason = row["block_reason"]
        if row["ticker"] in current_position_tickers:
            submit_allowed = False
            block_reason = "ALREADY_HELD"
        order_value = float(row["capped_position_value"])
        if order_value > float(configs["risk"]["risk"]["max_order_value_usd"]):
            submit_allowed = False
            block_reason = "MAX_ORDER_VALUE"
        plan_rows.append({
            "date": today_str(),
            "ticker": row["ticker"],
            "action": scan_row["action"],
            "current_position": 1 if row["ticker"] in current_position_tickers else 0,
            "target_position": row["shares"],
            "delta_shares": row["shares"],
            "estimated_entry": row["estimated_entry"],
            "suggested_stop": row["suggested_stop"],
            "risk_usd": row["estimated_risk_usd"],
            "position_value": row["capped_position_value"],
            "order_type": "LIMIT",
            "limit_price": row["estimated_entry"],
            "time_in_force": "DAY",
            "reason": scan_row["notes"],
            "strategy_name": configs["strategy"]["strategy"]["active"],
            "broker_mode": configs["broker"]["broker"]["active"],
            "submit_allowed": submit_allowed,
            "block_reason": block_reason,
        })
    order_plan_df = pd.DataFrame(plan_rows)
    save_order_plan(order_plan_df)
    return order_plan_df


def dry_run() -> None:
    broker, _ = _load_broker()
    if not isinstance(broker, DryRunBroker):
        console.print("[yellow]broker.active is not dry_run; generating dry-run style plan only if DRY_RUN=true.[/yellow]")
    order_plan_df = generate_order_plan()
    broker.connect()
    for _, row in order_plan_df.iterrows():
        if row["action"] != "BUY_CANDIDATE":
            continue
        order = OrderModel(
            ticker=row["ticker"],
            side="BUY",
            quantity=max(float(row["delta_shares"]), 0.0001),
            order_type="LIMIT",
            limit_price=float(row["limit_price"]),
            reason=row["reason"],
            broker_mode="dry_run",
            live_trading=False,
            paper_trading=True,
            dry_run=True,
        )
        broker.place_order(order)
    broker.disconnect()


def benchmark_summary(universe_cfg: dict, start: str, end: str) -> dict:
    spy = load_ticker_data("SPY")
    qqq = load_ticker_data("QQQ")
    spy = spy[(spy["Date"] >= start) & (spy["Date"] <= end)]
    qqq = qqq[(qqq["Date"] >= start) & (qqq["Date"] <= end)]
    spy_ret = float(spy["Close"].iloc[-1] / spy["Close"].iloc[0] - 1)
    qqq_ret = float(qqq["Close"].iloc[-1] / qqq["Close"].iloc[0] - 1)
    half_qqq_cash = qqq_ret * 0.5
    basket = []
    for ticker in universe_cfg["universe"]["stocks"]:
        df = load_ticker_data(ticker)
        df = df[(df["Date"] >= start) & (df["Date"] <= end)]
        basket.append(float(df["Close"].iloc[-1] / df["Close"].iloc[0] - 1))
    return {
        "SPY buy and hold": spy_ret,
        "QQQ buy and hold": qqq_ret,
        "50% QQQ + 50% cash": half_qqq_cash,
        "Equal-weight universe buy and hold": float(sum(basket) / len(basket)) if basket else 0.0,
    }


def backtest(start: str, end: str) -> None:
    configs = load_all_configs()
    metrics, trades_df, equity_curve_df = run_backtest(configs["universe"], configs["risk"], start, end)
    benchmarks = benchmark_summary(configs["universe"], start, end)
    save_backtest_reports(metrics, trades_df, equity_curve_df, benchmarks)
    save_equity_curve_chart(equity_curve_df, REPORTS_DIR / "charts" / f"{today_str()}_equity_curve.png")
    console.print(json.dumps(metrics, indent=2))


def ibkr_test_connection() -> None:
    configs = load_all_configs()
    _, safety_state = _load_broker()
    try:
        validate_broker_safety_config(safety_state)
        broker = IBKRBroker(safety_state)
        broker.connect()
        account = broker.get_account()
        positions = broker.get_positions()
        orders = broker.get_orders()
        account_id = configs["env"]["IBKR_ACCOUNT_ID"] or next(iter(account.keys()), "")
        masked = ("*" * max(len(account_id) - 4, 0) + account_id[-4:]) if account_id else "N/A"
        console.print({
            "status": "connected",
            "mode": "live" if safety_state.live_trading else ("paper" if not safety_state.dry_run else "dry_run"),
            "host": safety_state.host,
            "port": safety_state.port,
            "client_id": safety_state.client_id,
            "account_id": masked,
            "positions_count": len(positions),
            "open_orders_count": len(orders),
        })
        broker.disconnect()
    except Exception as exc:
        console.print(
            "IBKR connection unavailable. Likely causes: TWS / Gateway not started, API not enabled, wrong port, client_id conflict, wrong environment port, or missing 'Enable ActiveX and Socket Clients'."
        )
        console.print(str(exc))


def ibkr_sync() -> None:
    _, safety_state = _load_broker()
    try:
        broker = IBKRBroker(safety_state)
        broker.connect()
        account = broker.get_account()
        positions = broker.get_positions()
        orders = broker.get_orders()
        save_account_sync(account, positions, orders)
        broker.disconnect()
        console.print("IBKR sync completed.")
    except Exception as exc:
        console.print("IBKR sync skipped because connection is unavailable.")
        console.print(str(exc))


def ibkr_paper_test_order(ticker: str, quantity: float, limit_price: float) -> None:
    broker, safety_state = _load_broker()
    if safety_state.dry_run:
        console.print("DRY_RUN=true, generating simulated paper test order log only.")
        order = OrderModel(
            ticker=ticker,
            side="BUY",
            quantity=quantity,
            order_type="LIMIT",
            limit_price=limit_price,
            reason="ibkr_paper_test_order",
            broker_mode="dry_run",
            live_trading=False,
            paper_trading=True,
            dry_run=True,
        )
        DryRunBroker(safety_state).place_order(order)
        return
    if not safety_state.paper_trading or safety_state.live_trading:
        raise BrokerSafetyError("ibkr-paper-test-order requires PAPER_TRADING=true, DRY_RUN=false, LIVE_TRADING=false")
    if safety_state.port not in {7497, 4002}:
        raise BrokerSafetyError("ibkr-paper-test-order must use paper port 7497 or 4002")
    real_broker = IBKRBroker(safety_state)
    real_broker.connect()
    order = OrderModel(
        ticker=ticker,
        side="BUY",
        quantity=quantity,
        order_type="LIMIT",
        limit_price=limit_price,
        reason="ibkr_paper_test_order",
        broker_mode="ibkr_paper",
        live_trading=False,
        paper_trading=True,
        dry_run=False,
    )
    response = real_broker.place_order(order)
    real_broker.cancel_order(response["order_id"])
    real_broker.disconnect()
    console.print(response | {"cancelled": True})


def daily() -> None:
    download_data()
    compute_indicators()
    scan_df = scan()
    risk_df = run_risk_check()
    configs = load_all_configs()
    broker_active = configs["broker"]["broker"]["active"]
    current_positions = []
    if broker_active == "ibkr_paper":
        try:
            _, safety_state = _load_broker()
            broker = IBKRBroker(safety_state)
            broker.connect()
            current_positions = broker.get_positions()
            save_account_sync(broker.get_account(), current_positions, broker.get_orders())
            broker.disconnect()
        except Exception as exc:
            console.print(f"IBKR unavailable, continuing local daily flow: {exc}")
    elif broker_active == "ibkr_live":
        raise BrokerSafetyError("daily refuses ibkr_live by default unless all live safety conditions are manually enabled")
    order_plan_df = generate_order_plan(current_positions=current_positions)
    if broker_active == "dry_run":
        dry_run()
    daily_report_path = REPORTS_DIR / "daily" / f"{today_str()}_daily_report.md"
    lines = [
        f"# Daily Report {today_str()}",
        "",
        f"- broker_mode: {broker_active}",
        f"- scan_rows: {len(scan_df)}",
        f"- buy_candidates: {int((scan_df['action'] == 'BUY_CANDIDATE').sum())}",
        f"- watch_count: {int((scan_df['action'] == 'WATCH').sum())}",
        f"- order_plan_rows: {len(order_plan_df)}",
        f"- blocked_orders: {int((order_plan_df['submit_allowed'] == False).sum()) if not order_plan_df.empty else 0}",
        "",
        "## Top Scores",
        scan_df.head(5).to_markdown(index=False),
        "",
        "## Order Plan",
        order_plan_df.to_markdown(index=False) if not order_plan_df.empty else "No orders",
        "",
        "## Risk Notes",
    ]
    for _, row in scan_df.iterrows():
        lines.append(f"- {row['ticker']}: {row['notes']}")
    daily_report_path.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"Daily workflow completed. Report: {daily_report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="US stock quant system CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("download-data")
    subparsers.add_parser("compute-indicators")
    subparsers.add_parser("scan")
    subparsers.add_parser("risk-check")
    backtest_parser = subparsers.add_parser("backtest")
    backtest_parser.add_argument("--start", required=True)
    backtest_parser.add_argument("--end", required=True)
    subparsers.add_parser("dry-run")
    subparsers.add_parser("ibkr-test-connection")
    subparsers.add_parser("ibkr-sync")
    ibkr_order_parser = subparsers.add_parser("ibkr-paper-test-order")
    ibkr_order_parser.add_argument("--ticker", required=True)
    ibkr_order_parser.add_argument("--quantity", type=float, required=True)
    ibkr_order_parser.add_argument("--limit-price", type=float, required=True)
    subparsers.add_parser("daily")
    return parser


def main() -> None:
    ensure_directories()
    setup_logger()
    args = build_parser().parse_args()
    if args.command == "download-data":
        download_data()
    elif args.command == "compute-indicators":
        compute_indicators()
    elif args.command == "scan":
        scan()
    elif args.command == "risk-check":
        run_risk_check()
    elif args.command == "backtest":
        backtest(args.start, args.end)
    elif args.command == "dry-run":
        dry_run()
    elif args.command == "ibkr-test-connection":
        ibkr_test_connection()
    elif args.command == "ibkr-sync":
        ibkr_sync()
    elif args.command == "ibkr-paper-test-order":
        ibkr_paper_test_order(args.ticker, args.quantity, args.limit_price)
    elif args.command == "daily":
        daily()


if __name__ == "__main__":
    main()
