from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def save_equity_curve_chart(equity_curve_df: pd.DataFrame, output_path) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(pd.to_datetime(equity_curve_df["date"]), equity_curve_df["equity"])
    plt.title("Strategy Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
