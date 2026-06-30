from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def validate_ohlcv(df: pd.DataFrame) -> ValidationResult:
    issues: list[str] = []
    if df.empty:
        issues.append("empty_dataframe")
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        issues.append(f"missing_columns:{','.join(missing)}")
    if "Date" in df.columns and df["Date"].duplicated().any():
        issues.append("duplicate_dates")
    if {"High", "Low"}.issubset(df.columns) and (df["High"] < df["Low"]).any():
        issues.append("high_below_low")
    if "Close" in df.columns and (df["Close"] <= 0).any():
        issues.append("close_non_positive")
    if "Volume" in df.columns and (df["Volume"] < 0).any():
        issues.append("negative_volume")
    return ValidationResult(passed=not issues, issues=issues)
