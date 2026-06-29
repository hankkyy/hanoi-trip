from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
MOCK_DIR = DATA_DIR / "mock"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"


def ensure_directories() -> None:
    for path in [
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        CACHE_DIR,
        MOCK_DIR,
        REPORTS_DIR / "daily",
        REPORTS_DIR / "backtests",
        REPORTS_DIR / "charts",
        REPORTS_DIR / "account",
        REPORTS_DIR / "orders",
        LOGS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
