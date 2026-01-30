import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.db import Database
from core.settings import load_settings
from ui.main_window import MainWindow
from ui.style import APP_STYLE


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    settings = load_settings(Path.cwd())
    db_path = settings.data_dir / "portfolio.db"
    db = Database(db_path)
    window = MainWindow(db=db, settings=settings)
    window.show()
    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
