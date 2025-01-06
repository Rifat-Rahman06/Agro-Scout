from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtGui import QTextCursor
from datetime import datetime
from widget.view import ViewWindow
import sys, random

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.view = ViewWindow()
        self.setCentralWidget(self.view)
        self.view.get_log_suggestion.connect(self.process_suggestion)
        QTimer().singleShot(5000, self.add_multiple_logs)
    #     self.timer = QTimer()
    #     self.timer.timeout.connect(self.set_random_position)
    #     self.timer.start(5000)

    # def set_random_position(self):
    #     random_lat = random.uniform(-90, 90)
    #     random_lon = random.uniform(-180, 180)

    def process_suggestion(self, n, p, k, water, disease, lat, lon):

        self.view.set_log_suggestion(f"Suggestion is here actually okay for {n}, {p}, {k}, {water}, {disease}, {lat}, {lon}")

    def add_multiple_logs(self):
        logs = [
            ("Disease 1", 12.345, 12.345, 20, 30, 40, 50),
            ("Disease 2", 13.456, 14.567, 25, 35, 45, 55),
            ("Disease 3", 15.678, 16.789, 30, 40, 50, 60),
            ("Disease 4", 17.890, 18.901, 35, 45, 55, 65),
            ("Disease 5", 19.012, 20.123, 40, 50, 60, 70),
            ("Disease 6", 21.234, 22.345, 45, 55, 65, 75),
            ("Disease 7", 23.456, 24.567, 50, 60, 70, 80),
            ("Disease 8", 25.678, 26.789, 55, 65, 75, 85),
            ("Disease 9", 27.890, 28.901, 60, 70, 80, 90),
            ("Disease 10", 29.012, 30.123, 65, 75, 85, 95)
        ]

        for log in logs:
            disease_name, lat, lon, nitrogen, phosphorus, potassium, water = log
            self.view.add_log(disease_name, lat, lon, nitrogen, phosphorus, potassium, water, datetime.now().strftime("%H:%M"))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    exit(app.exec())
