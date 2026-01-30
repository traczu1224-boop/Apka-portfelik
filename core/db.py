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

    def import_transactions_csv(self, path: Path) -> int:
        count = 0
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                self.add_transaction(
                    symbol=row["symbol"],
                    trade_date=row["trade_date"],
                    quantity=float(row["quantity"]),
                    price=float(row["price"]),
                    currency=row["currency"],
                    fee=float(row.get("fee", 0) or 0),
                )
                count += 1
        return count

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
