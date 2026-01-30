from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QDateEdit,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QHeaderView

from core.db import Database
from ui.transaction_dialog import TransactionDialog


class TransactionsTab(QWidget):
    def __init__(self, db: Database, on_change) -> None:
        super().__init__()
        self.db = db
        self.on_change = on_change

        self.symbol_input = QLineEdit()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(6)
        self.quantity_input.setMaximum(1e9)
        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(6)
        self.price_input.setMaximum(1e9)
        self.currency_input = QLineEdit("PLN")
        self.fee_input = QDoubleSpinBox()
        self.fee_input.setDecimals(6)
        self.fee_input.setMaximum(1e9)

        title = QLabel("Transakcje")
        title.setObjectName("SectionTitle")
        description = QLabel("Dodaj zakup akcji i zarządzaj historią transakcji.")
        description.setObjectName("MutedText")

        form_layout = QFormLayout()
        form_layout.addRow("Symbol", self.symbol_input)
        form_layout.addRow("Data", self.date_input)
        form_layout.addRow("Ilość", self.quantity_input)
        form_layout.addRow("Cena", self.price_input)
        form_layout.addRow("Waluta", self.currency_input)
        form_layout.addRow("Prowizja", self.fee_input)

        add_button = QPushButton("Dodaj transakcję")
        add_button.clicked.connect(self.add_transaction)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Symbol", "Data", "Ilość", "Cena", "Waluta", "Prowizja"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        edit_button = QPushButton("Edytuj")
        delete_button = QPushButton("Usuń")
        edit_button.clicked.connect(self.edit_transaction)
        delete_button.clicked.connect(self.delete_transaction)

        import_button = QPushButton("Import CSV")
        export_button = QPushButton("Eksport CSV")
        import_button.clicked.connect(self.import_csv)
        export_button.clicked.connect(self.export_csv)

        button_row = QHBoxLayout()
        button_row.addWidget(add_button)
        button_row.addStretch()
        button_row.addWidget(edit_button)
        button_row.addWidget(delete_button)
        button_row.addWidget(import_button)
        button_row.addWidget(export_button)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.addLayout(form_layout)
        form_card_layout.addLayout(button_row)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(form_card)
        layout.addWidget(self.table)
        layout.setStretch(3, 1)
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        transactions = self.db.list_transactions()
        self.table.setRowCount(len(transactions))
        for row_idx, tx in enumerate(transactions):
            values = [
                str(tx.id),
                tx.symbol,
                tx.trade_date,
                f"{tx.quantity:.6f}",
                f"{tx.price:.6f}",
                tx.currency,
                f"{tx.fee:.6f}",
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_idx in (3, 4, 6):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

    def add_transaction(self) -> None:
        symbol = self.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "Błąd", "Podaj symbol.")
            return
        self.db.add_transaction(
            symbol=symbol,
            trade_date=self.date_input.date().toString("yyyy-MM-dd"),
            quantity=self.quantity_input.value(),
            price=self.price_input.value(),
            currency=self.currency_input.text().strip(),
            fee=self.fee_input.value(),
        )
        self.refresh()
        self.on_change()

    def _selected_transaction_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return int(self.table.item(row, 0).text())

    def edit_transaction(self) -> None:
        transaction_id = self._selected_transaction_id()
        if transaction_id is None:
            QMessageBox.information(self, "Edycja", "Wybierz transakcję.")
            return
        tx = next(
            (t for t in self.db.list_transactions() if t.id == transaction_id), None
        )
        if not tx:
            return
        dialog = TransactionDialog(self)
        dialog.set_values(
            symbol=tx.symbol,
            trade_date=tx.trade_date,
            quantity=tx.quantity,
            price=tx.price,
            currency=tx.currency,
            fee=tx.fee,
        )
        if dialog.exec() == dialog.Accepted:
            values = dialog.get_values()
            self.db.update_transaction(transaction_id=transaction_id, **values)
            self.refresh()
            self.on_change()

    def delete_transaction(self) -> None:
        transaction_id = self._selected_transaction_id()
        if transaction_id is None:
            QMessageBox.information(self, "Usuń", "Wybierz transakcję.")
            return
        self.db.delete_transaction(transaction_id)
        self.refresh()
        self.on_change()

    def import_csv(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", str(Path.cwd()), "CSV Files (*.csv)"
        )
        if not path_str:
            return
        count = self.db.import_transactions_csv(Path(path_str))
        QMessageBox.information(self, "Import", f"Zaimportowano {count} transakcji.")
        self.refresh()
        self.on_change()

    def export_csv(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Eksport CSV", str(Path.cwd()), "CSV Files (*.csv)"
        )
        if not path_str:
            return
        self.db.export_transactions_csv(Path(path_str))
        QMessageBox.information(self, "Eksport", "Zapisano plik CSV.")
