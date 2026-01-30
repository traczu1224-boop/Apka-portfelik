from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.settings import AppSettings, save_settings


class SettingsTab(QWidget):
    def __init__(self, app_settings: AppSettings, on_save) -> None:
        super().__init__()
        self.app_settings = app_settings
        self.on_save = on_save

        self.data_dir_input = QLineEdit(str(app_settings.data_dir))
        self.browse_button = QPushButton("Wybierz")
        self.browse_button.clicked.connect(self.select_folder)

        self.min_interval_input = QSpinBox()
        self.min_interval_input.setMinimum(1)
        self.min_interval_input.setMaximum(1440)
        self.min_interval_input.setValue(app_settings.min_interval_minutes)

        self.eod_only_check = QCheckBox("Używaj tylko EOD (close)")
        self.eod_only_check.setChecked(app_settings.eod_only)

        self.save_button = QPushButton("Zapisz ustawienia")
        self.save_button.clicked.connect(self.save)

        title = QLabel("Ustawienia")
        title.setObjectName("SectionTitle")
        description = QLabel("Skonfiguruj folder danych i częstotliwość pobrań.")
        description.setObjectName("MutedText")

        form = QFormLayout()
        data_row = QHBoxLayout()
        data_row.addWidget(self.data_dir_input)
        data_row.addWidget(self.browse_button)
        form.addRow("Folder danych", data_row)
        form.addRow("Limit pobrań (min)", self.min_interval_input)
        form.addRow("", self.eod_only_check)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.addLayout(form)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(form_card)
        layout.addWidget(self.save_button)
        layout.addStretch()
        self.setLayout(layout)

    def select_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Folder danych", str(self.app_settings.data_dir)
        )
        if directory:
            self.data_dir_input.setText(directory)

    def save(self) -> None:
        self.app_settings.data_dir = Path(self.data_dir_input.text()).expanduser()
        self.app_settings.min_interval_minutes = int(self.min_interval_input.value())
        self.app_settings.eod_only = self.eod_only_check.isChecked()
        save_settings(self.app_settings)
        QMessageBox.information(self, "Ustawienia", "Zapisano ustawienia.")
        self.on_save()
