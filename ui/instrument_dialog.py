from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class InstrumentDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Metadane instrumentu")

        self.symbol_input = QLineEdit()
        self.symbol_input.setReadOnly(True)
        self.sector_input = QLineEdit()
        self.tags_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Symbol", self.symbol_input)
        form.addRow("Sektor", self.sector_input)
        form.addRow("Tagi (oddziel przecinkiem)", self.tags_input)

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

    def set_values(self, symbol: str, sector: str, tags: str) -> None:
        self.symbol_input.setText(symbol)
        self.sector_input.setText(sector)
        self.tags_input.setText(tags)

    def get_values(self) -> dict:
        return {
            "sector": self.sector_input.text().strip(),
            "tags": self.tags_input.text().strip(),
        }
