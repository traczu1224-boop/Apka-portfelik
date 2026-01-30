from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.calculations import compute_portfolio_history
from core.db import Database
from core.returns import compute_returns


class ReturnsTab(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        description = QLabel(
            "TWR - stopa time-weighted (ignoruje wpłaty), MWR - XIRR (cashflow)."
        )
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Okres", "TWR %", "MWR (XIRR) %"])

        layout = QVBoxLayout()
        layout.addWidget(description)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        transactions = self.db.list_transactions()
        prices_by_symbol = {
            symbol: self.db.get_price_series(symbol)
            for symbol in {tx.symbol for tx in transactions}
        }
        history = compute_portfolio_history(transactions, prices_by_symbol)
        results = compute_returns(history, transactions)

        self.table.setRowCount(len(results))
        for row_idx, result in enumerate(results):
            row = [
                result.label,
                f"{result.twr:.2f}" if result.twr is not None else "brak danych",
                f"{result.mwr:.2f}" if result.mwr is not None else "brak danych",
            ]
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(value)
                if col_idx > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
