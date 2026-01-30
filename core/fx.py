import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests

from core.db import Database


NBP_TABLE_A_URL = "https://api.nbp.pl/api/exchangerates/tables/A?format=json"


@dataclass
class FxUpdateResult:
    message: str
    updated: int
    date: Optional[str]


class FxRateService:
    def __init__(self, db: Database, min_interval_hours: int = 12) -> None:
        self.db = db
        self.min_interval_hours = min_interval_hours

    def _should_skip(self, force: bool) -> bool:
        if force:
            return False
        last_update = self.db.get_metadata("last_fx_update")
        if not last_update:
            return False
        try:
            last_dt = datetime.fromisoformat(last_update)
        except ValueError:
            return False
        return (datetime.utcnow() - last_dt).total_seconds() < self.min_interval_hours * 3600

    def update_rates(self, force: bool = False) -> FxUpdateResult:
        if self._should_skip(force):
            rates = self.db.get_fx_rates()
            date = None
            if rates:
                date = next(iter(rates.values())).date
            result = FxUpdateResult(message="Pominięto (limit pobrań)", updated=0, date=date)
            self._log_update(result)
            return result
        response = None
        for attempt in range(2):
            try:
                response = requests.get(NBP_TABLE_A_URL, timeout=10)
                response.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 1:
                    result = FxUpdateResult(
                        message="Błąd pobierania kursów NBP",
                        updated=0,
                        date=None,
                    )
                    self._log_update(result)
                    return result
                time.sleep(1)
        if response is None:
            result = FxUpdateResult(
                message="Błąd pobierania kursów NBP",
                updated=0,
                date=None,
            )
            self._log_update(result)
            return result

        data = response.json()
        if not data:
            result = FxUpdateResult(message="Brak danych kursów", updated=0, date=None)
            self._log_update(result)
            return result
        table = data[0]
        effective_date = table.get("effectiveDate")
        updated = 0
        self.db.upsert_fx_rate("PLN", 1.0, effective_date or "", "NBP")
        updated += 1
        for rate in table.get("rates", []):
            code = rate.get("code")
            mid = rate.get("mid")
            if not code or mid is None:
                continue
            self.db.upsert_fx_rate(code.upper(), float(mid), effective_date or "", "NBP")
            updated += 1
        self.db.set_metadata("last_fx_update", datetime.utcnow().isoformat())
        result = FxUpdateResult(message="Zaktualizowano", updated=updated, date=effective_date)
        self._log_update(result)
        return result

    def _log_update(self, result: FxUpdateResult) -> None:
        self.db.add_update_log(
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
            symbol="FX",
            message=result.message,
            rows_added=result.updated,
            last_date=result.date,
            source="NBP",
        )
