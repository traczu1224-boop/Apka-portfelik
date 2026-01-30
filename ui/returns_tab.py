from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.calculations import compute_portfolio_history
from core.db import Database
from core.returns import compute_returns


class ReturnsTab(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        title = QLabel("Zwroty portfela")
        title.setObjectName("SectionTitle")
        description = QLabel(
            "TWR - stopa time-weighted (ignoruje wpłaty), MWR - XIRR (cashflow)."
        )
        description.setObjectName("MutedText")

        self.summary_card = QFrame()
        self.summary_card.setObjectName("Card")
        self.summary_layout = QGridLayout(self.summary_card)
        self.summary_labels: list[tuple[QLabel, QLabel]] = []
        for idx, label in enumerate(["1M", "3M", "6M", "1Y", "YTD", "Od początku"]):
            name = QLabel(label)
            name.setObjectName("MutedText")
            value = QLabel("-")
            value.setObjectName("SectionTitle")
            self.summary_layout.addWidget(name, 0, idx)
            self.summary_layout.addWidget(value, 1, idx)
            self.summary_labels.append((name, value))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Okres", "TWR %", "MWR (XIRR) %"])

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.summary_card)
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

        summary_map = {result.label: result for result in results}
        for label, value_label in self.summary_labels:
            result = summary_map.get(label.text())
            if result and result.twr is not None:
                value_label.setText(f"{result.twr:.2f}%")
            else:
                value_label.setText("-")
