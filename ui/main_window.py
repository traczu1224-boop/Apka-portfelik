from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

APP_STYLESHEET = """
QMainWindow {
    background: #f5f7fb;
    color: #0f172a;
    font-family: "Inter", "Segoe UI", "Arial";
}
QTabWidget::pane {
    border: none;
}
QTabBar::tab {
    background: #e2e8f0;
    color: #475569;
    padding: 10px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #0f172a;
    font-weight: 600;
}
QTabBar::tab:hover {
    background: #dbeafe;
    color: #1d4ed8;
}
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 14px;
    padding: 12px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #0f172a;
    font-weight: 600;
}
QFrame#metricCard {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}
QLabel#sectionTitle {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
}
QLabel#sectionSubtitle {
    color: #64748b;
}
QLabel#metricValue {
    font-size: 18px;
    font-weight: 700;
    color: #1d4ed8;
}
QLabel#metricLabel {
    color: #64748b;
}
QLabel#emptyState {
    color: #94a3b8;
    font-style: italic;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #94a3b8;
}
QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 8px;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    gridline-color: #e2e8f0;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
    alternate-background-color: #f8fafc;
}
QHeaderView::section {
    background: #f1f5f9;
    color: #475569;
    border: none;
    padding: 8px;
    font-weight: 600;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5f5;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
}
"""

from core.db import Database
from core.prices import PriceService
from core.settings import AppSettings
from ui.portfolio_tab import PortfolioTab
from ui.returns_tab import ReturnsTab
from ui.settings_tab import SettingsTab
from ui.transactions_tab import TransactionsTab


class MainWindow(QMainWindow):
    def __init__(self, db: Database, settings: AppSettings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.price_service = PriceService(
            db=self.db, min_interval_minutes=self.settings.min_interval_minutes
        )

        self.tabs = QTabWidget()
        self.transactions_tab = TransactionsTab(db=self.db, on_change=self.refresh_all)
        self.portfolio_tab = PortfolioTab(db=self.db, price_service=self.price_service)
        self.returns_tab = ReturnsTab(db=self.db)
        self.settings_tab = SettingsTab(
            app_settings=self.settings, on_save=self.reload_settings
        )

        self.tabs.addTab(self.transactions_tab, "Transakcje")
        self.tabs.addTab(self.portfolio_tab, "Portfel")
        self.tabs.addTab(self.returns_tab, "Zwroty")
        self.tabs.addTab(self.settings_tab, "Ustawienia")
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)
        self.setWindowTitle("Apka Portfelik - lokalny tracker portfela")
        self.resize(1200, 800)
        self.setStyleSheet(APP_STYLESHEET)

    def refresh_all(self) -> None:
        symbols = {tx.symbol for tx in self.db.list_transactions()}
        for symbol in symbols:
            self.price_service.update_symbol(symbol, force=False)
        self.transactions_tab.refresh()
        self.portfolio_tab.refresh()
        self.returns_tab.refresh()

    def reload_settings(self) -> None:
        new_db_path = self.settings.data_dir / "portfolio.db"
        if new_db_path != self.db.db_path:
            self.db.close()
            self.db = Database(new_db_path)
            self.transactions_tab.db = self.db
            self.portfolio_tab.db = self.db
            self.returns_tab.db = self.db
            self.price_service.db = self.db
        self.price_service.min_interval_minutes = self.settings.min_interval_minutes
        QMessageBox.information(self, "Ustawienia", "Zastosowano nowe ustawienia.")
        self.refresh_all()
