from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.db import Database


class UpdatesTab(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        title = QLabel("Log aktualizacji")
        title.setObjectName("SectionTitle")
        description = QLabel("Historia pobrań notowań i kursów.")
        description.setObjectName("MutedText")

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Czas", "Symbol", "Źródło", "Wynik", "Dodane", "Data notowań"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        logs = self.db.list_update_logs(limit=300)
        self.table.setRowCount(len(logs))
        for row_idx, entry in enumerate(logs):
            values = [
                entry.timestamp,
                entry.symbol,
                entry.source,
                entry.message,
                str(entry.rows_added),
                entry.last_date or "-",
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_idx in (4,):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
