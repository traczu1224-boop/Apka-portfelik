import csv
import io
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests

from core.db import Database


STOOQ_HISTORY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"


@dataclass
class PriceUpdateResult:
    symbol: str
    rows_added: int
    message: str
    last_date: Optional[str]


class PriceService:
    def __init__(self, db: Database, min_interval_minutes: int = 15) -> None:
        self.db = db
        self.min_interval_minutes = min_interval_minutes

    def _should_skip(self, symbol: str, force: bool) -> bool:
        if force:
            return False
        last_update_key = f"last_update:{symbol}"
        last_update = self.db.get_metadata(last_update_key)
        if not last_update:
            return False
        try:
            last_dt = datetime.fromisoformat(last_update)
        except ValueError:
            return False
        return (datetime.utcnow() - last_dt).total_seconds() < self.min_interval_minutes * 60

    def update_symbol(self, symbol: str, force: bool = False, log: bool = True) -> PriceUpdateResult:
        if self._should_skip(symbol, force=force):
            latest = self.db.get_latest_price(symbol)
            result = PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Pominięto (limit pobrań)",
                last_date=latest.date if latest else None,
            )
            if log:
                self._log_update(result)
            return result
        url = STOOQ_HISTORY_URL.format(symbol=symbol.lower())
        response = None
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                if attempt == 1:
                    result = PriceUpdateResult(
                        symbol=symbol,
                        rows_added=0,
                        message=f"Błąd pobierania: {exc}",
                        last_date=None,
                    )
                    if log:
                        self._log_update(result)
                    return result
                time.sleep(1)
        if response is None:
            result = PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Błąd pobierania: brak odpowiedzi",
                last_date=None,
            )
            if log:
                self._log_update(result)
            return result

        if "Date" not in response.text:
            result = PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Brak danych - sprawdź ticker/sufiks Stooq",
                last_date=None,
            )
            if log:
                self._log_update(result)
            return result

        rows = self._parse_csv(response.text)
        if not rows:
            result = PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Brak danych - sprawdź ticker/sufiks Stooq",
                last_date=None,
            )
            if log:
                self._log_update(result)
            return result
        rows_added = self.db.upsert_prices(symbol, rows)
        self.db.set_metadata(f"last_update:{symbol}", datetime.utcnow().isoformat())
        latest_date = rows[-1]["date"]
        result = PriceUpdateResult(
            symbol=symbol,
            rows_added=rows_added,
            message="Zaktualizowano",
            last_date=latest_date,
        )
        if log:
            self._log_update(result)
        return result

    def _log_update(self, result: PriceUpdateResult) -> None:
        self.db.add_update_log(
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
            symbol=result.symbol,
            message=result.message,
            rows_added=result.rows_added,
            last_date=result.last_date,
            source="stooq",
        )

    def _parse_csv(self, content: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(content))
        rows: list[dict] = []
        for row in reader:
            try:
                close_value = row.get("Close")
                if close_value in (None, ""):
                    continue
                close = float(close_value)

                def parse_optional(value: str | None) -> Optional[float]:
                    if not value:
                        return None
                    try:
                        return float(value)
                    except ValueError:
                        return None

                rows.append(
                    {
                        "date": row["Date"],
                        "open": parse_optional(row.get("Open")),
                        "high": parse_optional(row.get("High")),
                        "low": parse_optional(row.get("Low")),
                        "close": close,
                        "volume": parse_optional(row.get("Volume")),
                        "source": "stooq",
                    }
                )
            except (KeyError, ValueError, TypeError):
                continue
        rows.sort(key=lambda item: item["date"])
        return rows
