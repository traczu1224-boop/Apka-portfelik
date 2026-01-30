APP_STYLE = """
QWidget {
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 11pt;
    color: #F5F7FB;
    background-color: #0F1116;
}
QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox, QComboBox {
    background-color: #1B2029;
    border: 1px solid #2A3140;
    border-radius: 6px;
    padding: 6px 8px;
    color: #F5F7FB;
}
QComboBox QAbstractItemView {
    background-color: #1B2029;
    color: #F5F7FB;
    selection-background-color: #2E6EEB;
}
QTableWidget {
    background-color: #141824;
    gridline-color: #2A3140;
    border: 1px solid #2A3140;
    border-radius: 8px;
}
QTableWidget::item {
    color: #F5F7FB;
}
QHeaderView::section {
    background-color: #1B2029;
    color: #C9D1DE;
    padding: 6px 8px;
    border: none;
}
QPushButton {
    background-color: #2E6EEB;
    border: none;
    border-radius: 6px;
    color: white;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #417DF2;
}
QPushButton:disabled {
    background-color: #283246;
    color: #7D8797;
}
QTabWidget::pane {
    border: 1px solid #1E2430;
    padding: 8px;
}
QTabBar::tab {
    background: #151925;
    padding: 8px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #1E2430;
    color: #FFFFFF;
}
QLabel#SectionTitle {
    font-size: 14pt;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#MutedText {
    color: #C0C7D6;
}
QCheckBox {
    color: #F5F7FB;
}
QFrame#Card {
    background-color: #151925;
    border: 1px solid #2A3140;
    border-radius: 12px;
}
"""
