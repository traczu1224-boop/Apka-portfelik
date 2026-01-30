from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.calculations import aggregate_positions, compute_portfolio_history
from core.db import Database
from core.prices import PriceService
from ui.widgets import MatplotlibChart


class PortfolioTab(QWidget):
    def __init__(self, db: Database, price_service: PriceService) -> None:
        super().__init__()
        self.db = db
        self.price_service = price_service

        self.info_label = QLabel("")
        self.refresh_button = QPushButton("Odśwież notowania")
        self.refresh_button.clicked.connect(self.refresh_prices)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Symbol",
                "Waluta",
                "Ilość",
                "Śr. koszt",
                "Bieżąca cena",
                "Wartość",
                "Zysk/strata",
                "%",
                "Data notowań",
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        self.pie_chart = MatplotlibChart()
        self.line_chart = MatplotlibChart(height=3)

        layout = QVBoxLayout()
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.info_label)
        layout.addWidget(self.table)
        layout.addWidget(self.pie_chart)
        layout.addWidget(self.line_chart)
        self.setLayout(layout)

        self.refresh()

    def refresh_prices(self) -> None:
        symbols = {tx.symbol for tx in self.db.list_transactions()}
        if not symbols:
            QMessageBox.information(self, "Notowania", "Brak symboli do pobrania.")
            return
        messages = []
        for symbol in symbols:
            result = self.price_service.update_symbol(symbol, force=True)
            messages.append(f"{symbol}: {result.message}")
        QMessageBox.information(self, "Notowania", "\n".join(messages))
        self.refresh()

    def refresh(self) -> None:
        transactions = self.db.list_transactions()
        latest_prices = {
            tx.symbol: self.db.get_latest_price(tx.symbol) for tx in transactions
        }
        positions = aggregate_positions(transactions, latest_prices)
        self.table.setRowCount(len(positions))

        currencies = defaultdict(float)
        for row_idx, pos in enumerate(positions):
            row_values = [
                pos.symbol,
                pos.currency,
                f"{pos.quantity:.6f}",
                f"{pos.average_cost:.4f}",
                f"{pos.last_price:.4f}" if pos.last_price is not None else "-",
                f"{pos.market_value:.2f}" if pos.market_value is not None else "-",
                f"{pos.profit_loss:.2f}" if pos.profit_loss is not None else "-",
                f"{pos.profit_loss_pct:.2f}%"
                if pos.profit_loss_pct is not None
                else "-",
                pos.last_price_date or "-",
            ]
            for col_idx, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if col_idx >= 2:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
            if pos.market_value is not None:
                currencies[pos.currency] += pos.market_value
        self.table.resizeColumnsToContents()

        if len(currencies) > 1:
            note = "W portfelu są różne waluty. Suma nie jest przeliczana." 
        else:
            note = ""
        last_dates = {pos.symbol: pos.last_price_date for pos in positions if pos.last_price_date}
        if last_dates:
            last_info = ", ".join(
                f"{symbol}: {date}" for symbol, date in last_dates.items()
            )
            note += f" Ostatnie daty notowań: {last_info}"
        self.info_label.setText(note)

        pie_labels = []
        pie_values = []
        for pos in positions:
            if pos.market_value:
                pie_labels.append(pos.symbol)
                pie_values.append(pos.market_value)
        self.pie_chart.plot_pie(pie_labels, pie_values)

        prices_by_symbol = {
            symbol: self.db.get_price_series(symbol)
            for symbol in {tx.symbol for tx in transactions}
        }
        history = compute_portfolio_history(transactions, prices_by_symbol)
        x_values = [point.date for point in history]
        y_values = [point.value for point in history]
        self.line_chart.plot_line(x_values, y_values)
