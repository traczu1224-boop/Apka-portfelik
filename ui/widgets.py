from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout


class MatplotlibChart(QWidget):
    def __init__(self, width: int = 5, height: int = 4, dpi: int = 100, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def clear(self) -> None:
        self.figure.clear()
        self.canvas.draw()

    def plot_pie(self, labels: list[str], values: list[float]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if values:
            ax.pie(values, labels=labels, autopct="%1.1f%%")
        ax.set_title("Udział w portfelu")
        self.canvas.draw()

    def plot_line(self, x_values: list[str], y_values: list[float]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if x_values and y_values:
            ax.plot(x_values, y_values, linewidth=1.5)
            ax.tick_params(axis="x", labelrotation=45)
        ax.set_title("Wartość portfela w czasie")
        ax.set_xlabel("Data")
        ax.set_ylabel("Wartość")
        self.figure.tight_layout()
        self.canvas.draw()
