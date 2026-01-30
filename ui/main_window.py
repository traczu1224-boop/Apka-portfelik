from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from core.db import Database
from core.fx import FxRateService
from core.prices import PriceService
from core.settings import AppSettings
from ui.portfolio_tab import PortfolioTab
from ui.returns_tab import ReturnsTab
from ui.settings_tab import SettingsTab
from ui.transactions_tab import TransactionsTab
from ui.updates_tab import UpdatesTab


class MainWindow(QMainWindow):
    def __init__(self, db: Database, settings: AppSettings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.price_service = PriceService(
            db=self.db, min_interval_minutes=self.settings.min_interval_minutes
        )
        self.fx_service = FxRateService(db=self.db)

        self.tabs = QTabWidget()
        self.transactions_tab = TransactionsTab(db=self.db, on_change=self.refresh_all)
        self.portfolio_tab = PortfolioTab(
            db=self.db, price_service=self.price_service, fx_service=self.fx_service
        )
        self.returns_tab = ReturnsTab(db=self.db)
        self.updates_tab = UpdatesTab(db=self.db)
        self.settings_tab = SettingsTab(
            app_settings=self.settings, on_save=self.reload_settings
        )

        self.tabs.addTab(self.transactions_tab, "Transakcje")
        self.tabs.addTab(self.portfolio_tab, "Portfel")
        self.tabs.addTab(self.returns_tab, "Zwroty")
        self.tabs.addTab(self.updates_tab, "Aktualizacje")
        self.tabs.addTab(self.settings_tab, "Ustawienia")
        self.setCentralWidget(self.tabs)
        self.setWindowTitle("Apka Portfelik - lokalny tracker portfela")
        self.resize(1200, 800)

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.refresh_all)
        self._refresh_timer_interval()
        self.auto_timer.start()

    def refresh_all(self) -> None:
        self.fx_service.update_rates(force=False)
        symbols = {tx.symbol for tx in self.db.list_transactions()}
        for symbol in symbols:
            self.price_service.update_symbol(symbol, force=False)
        self.transactions_tab.refresh()
        self.portfolio_tab.refresh()
        self.returns_tab.refresh()
        self.updates_tab.refresh()

    def reload_settings(self) -> None:
        new_db_path = self.settings.data_dir / "portfolio.db"
        if new_db_path != self.db.db_path:
            self.db.close()
            self.db = Database(new_db_path)
            self.transactions_tab.db = self.db
            self.portfolio_tab.db = self.db
            self.returns_tab.db = self.db
            self.price_service.db = self.db
            self.fx_service.db = self.db
            self.updates_tab.db = self.db
        self.price_service.min_interval_minutes = self.settings.min_interval_minutes
        self._refresh_timer_interval()
        QMessageBox.information(self, "Ustawienia", "Zastosowano nowe ustawienia.")
        self.refresh_all()

    def _refresh_timer_interval(self) -> None:
        interval_ms = max(self.settings.auto_refresh_minutes, 1) * 60 * 1000
        self.auto_timer.setInterval(interval_ms)
