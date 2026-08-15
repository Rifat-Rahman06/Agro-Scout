from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel
from utilities.code_binder import view_code
from utilities.icon_generator import icon
import json

class ViewWindow(QWebEngineView):
    get_area_suggestion = Signal(str, str, str, str)
    get_log_suggestion = Signal(str, str, str, str, str, str, str)
    autonomous_called = Signal(float, float, float, float)
    auto_stop = Signal()

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        channel = QWebChannel(self.page())
        channel.registerObject("bridge", self)
        self.page().setWebChannel(channel)
        self.loadFinished.connect(self.set_icon)
        self.setHtml(view_code())
    
    @Slot(float, float, float, float)
    def autonomous(self, lat1, lng1, lat2, lng2):
        self.autonomous_called.emit(lat1, lng1, lat2,lng2)

    @Slot()
    def stopp(self):
        self.auto_stop.emit()

    @Slot(str, str, str, str)
    def area_suggestion(self, n, p, k, water):
        self.get_area_suggestion.emit(n, p, k, water)

    def set_area_suggestion(self, str):
        self.page().runJavaScript(f'set_area_suggestion("{str}")')


    def add_log(self, disease_name, lat, lon, nitrogen, phosphorus, potassium, water, time_now):
        self.page().runJavaScript(
            f"""
            add_log("{disease_name}", {lat}, {lon}, {nitrogen}, {phosphorus}, {potassium}, {water}, "{time_now}");
        """
        )

    @Slot(str, str, str, str, str, str, str)
    def log_suggestion(self, n, p, k, water, lat, lon, disease_name):
        self.get_log_suggestion.emit(n, p, k, water, lat, lon, disease_name)

    def set_log_suggestion(self, str):
        escaped_str = str.replace("\n", "\\n").replace('"', '\\"')
        self.page().runJavaScript(f'set_log_suggestion("{escaped_str}")')


    @Slot()
    def sendFilePath(self):
        print('Selecting file')
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Select a File", "", "All Files (*)", options=options
        )
        if filePath:
            self.file_dir(filePath)

    def file_dir(self, dir):
        self.page().runJavaScript(f'file_dir("{dir}")')

    def set_icon(self):
        icon_ob = icon()
        icons_json = json.dumps(icon_ob.icons)
        js_code = f"set_icons({icons_json});"
        self.page().runJavaScript(js_code)

    def set_heading(self, angle):
        self.page().runJavaScript(f'set_heading({angle})')
        self.page().runJavaScript(f'compass({angle})')


    def set_battery(self, data):
        self.page().runJavaScript(f"set_battery({data})")

    def set_speed(self, data):
        self.page().runJavaScript(f"set_speed({data})")

    def set_spray(self, data):
        self.page().runJavaScript(f"set_spray({data})")

    def set_diseased_count(self, data):
        self.page().runJavaScript(f"set_diseased_count({data})")

    def set_tilt(self, x, y):
        self.page().runJavaScript(f"set_tilt({x}, {y})")

    def set_position(self, lat, lon):
        self.page().runJavaScript(f"set_position({lat}, {lon})")
        self.page().runJavaScript(f"update_location({lat}, {lon})")

    
    def add_data(self, lat, lon):
        self.page().runJavaScript(f'addBlinkingMarker({lat}, {lon})')
    
    def connection_status(self, state):
        self.page().runJavaScript(f"connection_status('{ 'Connected' if state else 'Disconnected' }')")

    def set_grid(self, index, n, p, k, w):
        self.page().runJavaScript(f'set_grid({index}, {n}, {p}, {k}, {w})')