from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.calculations import aggregate_positions, compute_portfolio_history
from core.db import Database
from core.fx import FxRateService
from core.prices import PriceService
from ui.instrument_dialog import InstrumentDialog
from ui.widgets import MatplotlibChart


class PortfolioTab(QWidget):
    def __init__(
        self, db: Database, price_service: PriceService, fx_service: FxRateService
    ) -> None:
        super().__init__()
        self.db = db
        self.price_service = price_service
        self.fx_service = fx_service

        title = QLabel("Portfel")
        title.setObjectName("SectionTitle")
        self.info_label = QLabel("")
        self.info_label.setObjectName("MutedText")
        self.fx_label = QLabel("")
        self.fx_label.setObjectName("MutedText")
        self.refresh_button = QPushButton("Odśwież notowania")
        self.refresh_button.clicked.connect(self.refresh_prices)
        self.edit_button = QPushButton("Edytuj metadane")
        self.edit_button.clicked.connect(self.edit_instrument)

        self.sector_filter = QComboBox()
        self.sector_filter.addItem("Wszystkie sektory")
        self.sector_filter.currentIndexChanged.connect(self.refresh)
        self.tag_filter = QLineEdit()
        self.tag_filter.setPlaceholderText("Filtr tagów (np. dividend, tech)")
        self.tag_filter.textChanged.connect(self.refresh)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            [
                "Symbol",
                "Waluta",
                "Sektor",
                "Tagi",
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

        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(self.pie_chart)
        chart_layout.addWidget(self.line_chart)

        layout = QVBoxLayout()
        layout.addWidget(title)
        top_row = QHBoxLayout()
        top_row.addWidget(self.refresh_button)
        top_row.addWidget(self.edit_button)
        top_row.addStretch()
        layout.addLayout(top_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Sektor"))
        filter_row.addWidget(self.sector_filter)
        filter_row.addWidget(QLabel("Tagi"))
        filter_row.addWidget(self.tag_filter)
        layout.addLayout(filter_row)
        layout.addWidget(self.info_label)
        layout.addWidget(self.fx_label)
        layout.addWidget(self.table)
        layout.addWidget(chart_card)
        self.setLayout(layout)

        self.refresh()

    def refresh_prices(self) -> None:
        symbols = {tx.symbol for tx in self.db.list_transactions()}
        if not symbols:
            QMessageBox.information(self, "Notowania", "Brak symboli do pobrania.")
            return
        messages = []
        self.fx_service.update_rates(force=True)
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
        instruments = {info.symbol: info for info in self.db.list_instruments()}
        self._refresh_sector_filter(instruments.values())

        selected_sector = self.sector_filter.currentText()
        tag_filter = self.tag_filter.text().strip().lower()
        filtered_positions = []
        for pos in positions:
            instrument = instruments.get(pos.symbol)
            sector = instrument.sector if instrument else ""
            tags = instrument.tags if instrument else ""
            if selected_sector != "Wszystkie sektory" and sector != selected_sector:
                continue
            if tag_filter:
                tags_lower = {tag.strip().lower() for tag in tags.split(",") if tag.strip()}
                if tag_filter not in tags_lower:
                    continue
            filtered_positions.append(pos)
        positions = filtered_positions

        self.table.setRowCount(len(positions))

        currencies = defaultdict(float)
        for row_idx, pos in enumerate(positions):
            instrument = instruments.get(pos.symbol)
            sector = instrument.sector if instrument else ""
            tags = instrument.tags if instrument else ""
            row_values = [
                pos.symbol,
                pos.currency,
                sector,
                tags,
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
                if col_idx >= 4:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
            if pos.market_value is not None:
                currencies[pos.currency] += pos.market_value
        self.table.resizeColumnsToContents()

        fx_rates = self.db.get_fx_rates()
        total_pln = 0.0
        missing_rates = []
        for currency, value in currencies.items():
            rate = fx_rates.get(currency)
            if rate is None:
                missing_rates.append(currency)
                continue
            total_pln += value * rate.rate
        fx_note = f"Suma w PLN: {total_pln:,.2f}" if currencies else "Suma w PLN: -"
        if missing_rates:
            fx_note += f" (brak kursów: {', '.join(sorted(missing_rates))})"
        self.fx_label.setText(fx_note)

        if len(currencies) > 1:
            note = "W portfelu są różne waluty. Suma w PLN używa kursów NBP."
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
            for symbol in {pos.symbol for pos in positions}
        }
        filtered_transactions = [tx for tx in transactions if tx.symbol in prices_by_symbol]
        history = compute_portfolio_history(filtered_transactions, prices_by_symbol)
        x_values = [point.date for point in history]
        y_values = [point.value for point in history]
        self.line_chart.plot_line(x_values, y_values)

    def _refresh_sector_filter(self, instruments) -> None:
        sectors = sorted({info.sector for info in instruments if info.sector})
        current = self.sector_filter.currentText()
        self.sector_filter.blockSignals(True)
        self.sector_filter.clear()
        self.sector_filter.addItem("Wszystkie sektory")
        for sector in sectors:
            self.sector_filter.addItem(sector)
        if current in sectors:
            self.sector_filter.setCurrentText(current)
        else:
            self.sector_filter.setCurrentIndex(0)
        self.sector_filter.blockSignals(False)

    def edit_instrument(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Metadane", "Wybierz pozycję.")
            return
        row = selected[0].row()
        symbol_item = self.table.item(row, 0)
        if symbol_item is None:
            return
        symbol = symbol_item.text()
        instrument = self.db.get_instrument(symbol)
        dialog = InstrumentDialog(self)
        dialog.set_values(
            symbol=symbol,
            sector=instrument.sector if instrument else "",
            tags=instrument.tags if instrument else "",
        )
        if dialog.exec() == dialog.Accepted:
            values = dialog.get_values()
            self.db.upsert_instrument(symbol, values["sector"], values["tags"])
            self.refresh()
