from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QDoubleSpinBox,
    QDateEdit,
    QVBoxLayout,
)


class TransactionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edycja transakcji")
        self.symbol_input = QLineEdit()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(6)
        self.quantity_input.setMaximum(1e9)
        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(6)
        self.price_input.setMaximum(1e9)
        self.currency_input = QLineEdit()
        self.fee_input = QDoubleSpinBox()
        self.fee_input.setDecimals(6)
        self.fee_input.setMaximum(1e9)

        form = QFormLayout()
        form.addRow("Symbol", self.symbol_input)
        form.addRow("Data", self.date_input)
        form.addRow("Ilość", self.quantity_input)
        form.addRow("Cena", self.price_input)
        form.addRow("Waluta", self.currency_input)
        form.addRow("Prowizja", self.fee_input)

        buttons = QHBoxLayout()
        save_button = QPushButton("Zapisz")
        cancel_button = QPushButton("Anuluj")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def set_values(
        self,
        symbol: str,
        trade_date: str,
        quantity: float,
        price: float,
        currency: str,
        fee: float,
    ) -> None:
        self.symbol_input.setText(symbol)
        self.date_input.setDate(QDate.fromString(trade_date, "yyyy-MM-dd"))
        self.quantity_input.setValue(quantity)
        self.price_input.setValue(price)
        self.currency_input.setText(currency)
        self.fee_input.setValue(fee)

    def get_values(self) -> dict:
        return {
            "symbol": self.symbol_input.text().strip().upper(),
            "trade_date": self.date_input.date().toString("yyyy-MM-dd"),
            "quantity": self.quantity_input.value(),
            "price": self.price_input.value(),
            "currency": self.currency_input.text().strip().upper(),
            "fee": self.fee_input.value(),
        }
