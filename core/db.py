import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class Transaction:
    id: int
    symbol: str
    trade_date: str
    quantity: float
    price: float
    currency: str
    fee: float


@dataclass
class PriceRow:
    id: int
    symbol: str
    date: str
    close: float
    open: float
    high: float
    low: float
    volume: float
    source: str


@dataclass
class ImportSummary:
    imported: int
    skipped: int
    errors: list[str]


@dataclass
class InstrumentInfo:
    symbol: str
    sector: str
    tags: str


@dataclass
class FxRate:
    currency: str
    rate: float
    date: str
    source: str


@dataclass
class UpdateLog:
    id: int
    timestamp: str
    symbol: str
    message: str
    rows_added: int
    last_date: Optional[str]
    source: str


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                fee REAL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                close REAL NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                volume REAL,
                source TEXT NOT NULL,
                UNIQUE(symbol, date)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS instruments (
                symbol TEXT PRIMARY KEY,
                sector TEXT,
                tags TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fx_rates (
                currency TEXT PRIMARY KEY,
                rate REAL NOT NULL,
                date TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS update_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                message TEXT NOT NULL,
                rows_added INTEGER NOT NULL,
                last_date TEXT,
                source TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def add_transaction(
        self,
        symbol: str,
        trade_date: str,
        quantity: float,
        price: float,
        currency: str,
        fee: float,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (symbol, trade_date, quantity, price, currency, fee)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (symbol, trade_date, quantity, price, currency, fee),
        )
        self.connection.commit()

    def update_transaction(
        self,
        transaction_id: int,
        symbol: str,
        trade_date: str,
        quantity: float,
        price: float,
        currency: str,
        fee: float,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE transactions
            SET symbol = ?, trade_date = ?, quantity = ?, price = ?, currency = ?, fee = ?
            WHERE id = ?
            """,
            (symbol, trade_date, quantity, price, currency, fee, transaction_id),
        )
        self.connection.commit()

    def delete_transaction(self, transaction_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.connection.commit()

    def list_transactions(self) -> list[Transaction]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            """SELECT id, symbol, trade_date, quantity, price, currency, fee
            FROM transactions
            ORDER BY trade_date ASC, id ASC"""
        ).fetchall()
        return [
            Transaction(
                id=row["id"],
                symbol=row["symbol"],
                trade_date=row["trade_date"],
                quantity=row["quantity"],
                price=row["price"],
                currency=row["currency"],
                fee=row["fee"] or 0.0,
            )
            for row in rows
        ]

    def import_transactions_csv(self, path: Path) -> ImportSummary:
        count = 0
        skipped = 0
        errors: list[str] = []
        required_fields = ["symbol", "trade_date", "quantity", "price", "currency"]
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=2):
                try:
                    missing = [
                        field for field in required_fields if not row.get(field)
                    ]
                    if missing:
                        raise ValueError(f"Brak pól: {', '.join(missing)}")
                    self.add_transaction(
                        symbol=row["symbol"].strip().upper(),
                        trade_date=row["trade_date"].strip(),
                        quantity=float(row["quantity"]),
                        price=float(row["price"]),
                        currency=row["currency"].strip().upper(),
                        fee=float(row.get("fee", 0) or 0),
                    )
                    count += 1
                except (KeyError, ValueError) as exc:
                    skipped += 1
                    errors.append(f"Wiersz {row_number}: {exc}")
        return ImportSummary(imported=count, skipped=skipped, errors=errors)

    def export_transactions_csv(self, path: Path) -> None:
        fieldnames = ["symbol", "trade_date", "quantity", "price", "currency", "fee"]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for transaction in self.list_transactions():
                writer.writerow(
                    {
                        "symbol": transaction.symbol,
                        "trade_date": transaction.trade_date,
                        "quantity": transaction.quantity,
                        "price": transaction.price,
                        "currency": transaction.currency,
                        "fee": transaction.fee,
                    }
                )

    def upsert_instrument(self, symbol: str, sector: str, tags: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO instruments (symbol, sector, tags)
            VALUES (?, ?, ?)
            """,
            (symbol, sector, tags),
        )
        self.connection.commit()

    def get_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        cursor = self.connection.cursor()
        row = cursor.execute(
            "SELECT symbol, sector, tags FROM instruments WHERE symbol = ?",
            (symbol,),
        ).fetchone()
        if not row:
            return None
        return InstrumentInfo(
            symbol=row["symbol"],
            sector=row["sector"] or "",
            tags=row["tags"] or "",
        )

    def list_instruments(self) -> list[InstrumentInfo]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            "SELECT symbol, sector, tags FROM instruments ORDER BY symbol ASC"
        ).fetchall()
        return [
            InstrumentInfo(
                symbol=row["symbol"],
                sector=row["sector"] or "",
                tags=row["tags"] or "",
            )
            for row in rows
        ]

    def upsert_fx_rate(self, currency: str, rate: float, date: str, source: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO fx_rates (currency, rate, date, source)
            VALUES (?, ?, ?, ?)
            """,
            (currency, rate, date, source),
        )
        self.connection.commit()

    def get_fx_rates(self) -> dict[str, FxRate]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            "SELECT currency, rate, date, source FROM fx_rates"
        ).fetchall()
        return {
            row["currency"]: FxRate(
                currency=row["currency"],
                rate=row["rate"],
                date=row["date"],
                source=row["source"],
            )
            for row in rows
        }

    def add_update_log(
        self,
        timestamp: str,
        symbol: str,
        message: str,
        rows_added: int,
        last_date: Optional[str],
        source: str,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO update_logs (timestamp, symbol, message, rows_added, last_date, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (timestamp, symbol, message, rows_added, last_date, source),
        )
        self.connection.commit()

    def list_update_logs(self, limit: int = 200) -> list[UpdateLog]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            """
            SELECT id, timestamp, symbol, message, rows_added, last_date, source
            FROM update_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            UpdateLog(
                id=row["id"],
                timestamp=row["timestamp"],
                symbol=row["symbol"],
                message=row["message"],
                rows_added=row["rows_added"],
                last_date=row["last_date"],
                source=row["source"],
            )
            for row in rows
        ]

    def upsert_prices(self, symbol: str, rows: Iterable[dict]) -> int:
        cursor = self.connection.cursor()
        count = 0
        for row in rows:
            cursor.execute(
                """
                INSERT OR REPLACE INTO prices
                (symbol, date, close, open, high, low, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    row["date"],
                    row["close"],
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    row.get("volume"),
                    row.get("source", "stooq"),
                ),
            )
            count += 1
        self.connection.commit()
        return count

    def get_price_series(self, symbol: str) -> list[PriceRow]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            """
            SELECT id, symbol, date, close, open, high, low, volume, source
            FROM prices
            WHERE symbol = ?
            ORDER BY date ASC
            """,
            (symbol,),
        ).fetchall()
        return [
            PriceRow(
                id=row["id"],
                symbol=row["symbol"],
                date=row["date"],
                close=row["close"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                volume=row["volume"],
                source=row["source"],
            )
            for row in rows
        ]

    def get_latest_price(self, symbol: str) -> Optional[PriceRow]:
        cursor = self.connection.cursor()
        row = cursor.execute(
            """
            SELECT id, symbol, date, close, open, high, low, volume, source
            FROM prices
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (symbol,),
        ).fetchone()
        if not row:
            return None
        return PriceRow(
            id=row["id"],
            symbol=row["symbol"],
            date=row["date"],
            close=row["close"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            volume=row["volume"],
            source=row["source"],
        )

    def get_metadata(self, key: str) -> Optional[str]:
        cursor = self.connection.cursor()
        row = cursor.execute(
            "SELECT value FROM metadata WHERE key = ?",
            (key,),
        ).fetchone()
        if row:
            return row["value"]
        return None

    def set_metadata(self, key: str, value: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
