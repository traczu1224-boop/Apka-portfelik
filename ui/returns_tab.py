from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "TWR pokazuje wyniki bez wpływu wpłat, MWR (XIRR) uwzględnia przepływy."
        )
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)

        self.twr_value = QLabel("-")
        self.twr_value.setObjectName("metricValue")
        self.twr_label = QLabel("TWR od początku")
        self.twr_label.setObjectName("metricLabel")
        self.mwr_value = QLabel("-")
        self.mwr_value.setObjectName("metricValue")
        self.mwr_label = QLabel("MWR (XIRR) od początku")
        self.mwr_label.setObjectName("metricLabel")
        self.periods_value = QLabel("0")
        self.periods_value.setObjectName("metricValue")
        self.periods_label = QLabel("Liczba okresów")
        self.periods_label.setObjectName("metricLabel")

        summary_group = QGroupBox("Podsumowanie")
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self._build_metric_card(self.twr_value, self.twr_label))
        summary_layout.addWidget(self._build_metric_card(self.mwr_value, self.mwr_label))
        summary_layout.addWidget(
            self._build_metric_card(self.periods_value, self.periods_label)
        )
        summary_group.setLayout(summary_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Okres", "TWR %", "MWR (XIRR) %"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.empty_state = QLabel(
            "Brak wystarczających danych. Dodaj transakcje i notowania, aby zobaczyć zwroty."
        )
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setObjectName("emptyState")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(summary_group)
        layout.addWidget(self.table)
        layout.addWidget(self.empty_state)
        self.setLayout(layout)

        self.refresh()

    def _build_metric_card(self, value_label: QLabel, name_label: QLabel) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(6)
        card_layout.addWidget(value_label)
        card_layout.addWidget(name_label)
        card.setLayout(card_layout)
        return card

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
        self._update_summary(results)
        has_results = bool(results)
        self.empty_state.setVisible(not has_results)
        self.table.setVisible(has_results)

    def _update_summary(self, results) -> None:
        if not results:
            self.twr_value.setText("-")
            self.mwr_value.setText("-")
            self.periods_value.setText("0")
            return

        summary = next(
            (
                result
                for result in results
                if "od początku" in result.label.lower()
            ),
            results[-1],
        )
        self.twr_value.setText(
            f"{summary.twr:.2f}%" if summary.twr is not None else "-"
        )
        self.mwr_value.setText(
            f"{summary.mwr:.2f}%" if summary.mwr is not None else "-"
        )
        self.periods_value.setText(str(len(results)))
