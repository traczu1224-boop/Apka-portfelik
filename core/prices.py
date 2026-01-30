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

    def update_symbol(self, symbol: str, force: bool = False) -> PriceUpdateResult:
        if self._should_skip(symbol, force=force):
            latest = self.db.get_latest_price(symbol)
            return PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Pominięto (limit pobrań)",
                last_date=latest.date if latest else None,
            )
        url = STOOQ_HISTORY_URL.format(symbol=symbol.lower())
        response = None
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                if attempt == 1:
                    return PriceUpdateResult(
                        symbol=symbol,
                        rows_added=0,
                        message=f"Błąd pobierania: {exc}",
                        last_date=None,
                    )
                time.sleep(1)
        if response is None:
            return PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Błąd pobierania: brak odpowiedzi",
                last_date=None,
            )

        if "Date" not in response.text:
            return PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Brak danych - sprawdź ticker/sufiks Stooq",
                last_date=None,
            )

        rows = self._parse_csv(response.text)
        if not rows:
            return PriceUpdateResult(
                symbol=symbol,
                rows_added=0,
                message="Brak danych - sprawdź ticker/sufiks Stooq",
                last_date=None,
            )
        rows_added = self.db.upsert_prices(symbol, rows)
        self.db.set_metadata(f"last_update:{symbol}", datetime.utcnow().isoformat())
        latest_date = rows[-1]["date"]
        return PriceUpdateResult(
            symbol=symbol,
            rows_added=rows_added,
            message="Zaktualizowano",
            last_date=latest_date,
        )

    def _parse_csv(self, content: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(content))
        rows: list[dict] = []
        for row in reader:
            try:
                rows.append(
                    {
                        "date": row["Date"],
                        "open": float(row["Open"]) if row.get("Open") else None,
                        "high": float(row["High"]) if row.get("High") else None,
                        "low": float(row["Low"]) if row.get("Low") else None,
                        "close": float(row["Close"]) if row.get("Close") else None,
                        "volume": float(row["Volume"]) if row.get("Volume") else None,
                        "source": "stooq",
                    }
                )
            except (KeyError, ValueError):
                continue
        rows.sort(key=lambda item: item["date"])
        return rows
