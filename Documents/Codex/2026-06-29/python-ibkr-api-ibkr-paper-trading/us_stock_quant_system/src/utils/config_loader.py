from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .paths import CONFIG_DIR, PROJECT_ROOT


load_dotenv(PROJECT_ROOT / ".env", override=False)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=1)
def load_all_configs() -> dict[str, Any]:
    return {
        "settings": _read_yaml(CONFIG_DIR / "settings.yaml"),
        "universe": _read_yaml(CONFIG_DIR / "universe.yaml"),
        "strategy": _read_yaml(CONFIG_DIR / "strategy.yaml"),
        "risk": _read_yaml(CONFIG_DIR / "risk.yaml"),
        "broker": _read_yaml(CONFIG_DIR / "broker.yaml"),
        "env": {
            "DRY_RUN": os.getenv("DRY_RUN", "true").lower() == "true",
            "PAPER_TRADING": os.getenv("PAPER_TRADING", "true").lower() == "true",
            "LIVE_TRADING": os.getenv("LIVE_TRADING", "false").lower() == "true",
            "CONFIRM_LIVE_TRADING": os.getenv("CONFIRM_LIVE_TRADING", ""),
            "IBKR_HOST": os.getenv("IBKR_HOST", "127.0.0.1"),
            "IBKR_PORT": int(os.getenv("IBKR_PORT", "7497")),
            "IBKR_CLIENT_ID": int(os.getenv("IBKR_CLIENT_ID", "101")),
            "IBKR_ACCOUNT_ID": os.getenv("IBKR_ACCOUNT_ID", ""),
            "AUTO_SUBMIT_PAPER_ORDERS": os.getenv("AUTO_SUBMIT_PAPER_ORDERS", "false").lower() == "true",
            "ALLOW_MARKET_ORDERS": os.getenv("ALLOW_MARKET_ORDERS", "false").lower() == "true",
            "ALLOW_FRACTIONAL_SHARES": os.getenv("ALLOW_FRACTIONAL_SHARES", "true").lower() == "true",
        },
    }


def reset_config_cache() -> None:
    load_all_configs.cache_clear()
