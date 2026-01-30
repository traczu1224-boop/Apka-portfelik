from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings


@dataclass
class AppSettings:
    data_dir: Path
    min_interval_minutes: int
    auto_refresh_minutes: int
    eod_only: bool


def load_settings(base_dir: Path) -> AppSettings:
    settings = QSettings("ApkaPortfelik", "PortfolioTracker")
    data_dir = Path(settings.value("data_dir", str(base_dir / "data")))
    min_interval = int(settings.value("min_interval", 15))
    auto_refresh = int(settings.value("auto_refresh", 30))
    eod_only = settings.value("eod_only", True, type=bool)
    return AppSettings(
        data_dir=data_dir,
        min_interval_minutes=min_interval,
        auto_refresh_minutes=auto_refresh,
        eod_only=eod_only,
    )


def save_settings(app_settings: AppSettings) -> None:
    settings = QSettings("ApkaPortfelik", "PortfolioTracker")
    settings.setValue("data_dir", str(app_settings.data_dir))
    settings.setValue("min_interval", app_settings.min_interval_minutes)
    settings.setValue("auto_refresh", app_settings.auto_refresh_minutes)
    settings.setValue("eod_only", app_settings.eod_only)
