from __future__ import annotations

import pandas as pd

from .position_sizing import calculate_position_size


def risk_check(scan_df: pd.DataFrame, universe_cfg: dict, risk_cfg: dict) -> pd.DataFrame:
    positions = []
    sectors = universe_cfg.get("sectors", {})
    for _, row in scan_df.iterrows():
        if row["action"] != "BUY_CANDIDATE":
            continue
        sector = sectors.get(row["ticker"], "Unknown")
        result = calculate_position_size(row, risk_cfg, sector, positions)
        positions.append({"ticker": result.ticker, "sector": sector})
        result_row = result.__dict__ | {"sector": sector}
        yield_row = pd.DataFrame([result_row])
        if "results" not in locals():
            results = yield_row
        else:
            results = pd.concat([results, yield_row], ignore_index=True)
    return results if "results" in locals() else pd.DataFrame(columns=[
        "ticker", "estimated_entry", "suggested_stop", "stop_distance_pct", "risk_amount",
        "raw_position_value", "capped_position_value", "shares", "estimated_risk_usd",
        "position_allowed", "block_reason", "sector",
    ])
