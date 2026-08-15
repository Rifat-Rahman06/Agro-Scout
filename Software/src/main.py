from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtGui import QTextCursor
from datetime import datetime
from PySide6.QtCore import QTimer
from utilities.Connection import connection
from utilities.suggestion import Suggestion
from widget.view import ViewWindow
import sys, random
import time
from PySide6.QtCore import QThread, Signal

class MyWorker(QThread):
    done = Signal(str)  

    def __init__(self, ai_instance, n, p, k, water, disease):
        super().__init__()
        self.ai_instance = ai_instance
        self.n = n
        self.p = p
        self.k = k
        self.water = water
        self.disease = disease

    def run(self):
        result = self.ai_instance.get_disease_suggestion([self.n, self.p, self.k, self.water], self.disease)
        self.done.emit(result)

class MyWorker_2(QThread):
    done = Signal(str)  

    def __init__(self, ai_instance, n, p, k, water):
        super().__init__()
        self.ai_instance = ai_instance
        self.n = n
        self.p = p
        self.k = k
        self.water = water

    def run(self):
        result = self.ai_instance.get_field_suggetion([self.n, self.p, self.k, self.water])
        self.done.emit(result)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.view = ViewWindow()
        self.setCentralWidget(self.view)
        self.lat = '23.7978814'
        self.lon = '90.4499017'
        self.plant_count = 0
        self.ai = Suggestion('YOUR_GROQ_API_KEY')

        self.connection = connection(4292, 60000, 115200)
        self.connection.has_data.connect(self.showdata)
        self.connection.active.connect(self.reciever_status)

        self.view.get_log_suggestion.connect(self.process_log_suggestion)
        self.view.get_area_suggestion.connect(self.process_area_suggestion)
        # QTimer().singleShot(5000, self.add_multiple_logs)
        self.view.autonomous_called.connect(self.autonomous)
        self.view.auto_stop.connect(self.stop_rover)

    def stop_rover(self):
        self.connection.write('x')

    def autonomous(self, lat1, lon1, lat2, lon2):
        self.plant_count = 0
        self.view.set_diseased_count(self.plant_count)
        self.connection.write(f'a{lat1}')

        self.timer1 = QTimer()
        self.timer1.setSingleShot(True)  
        self.timer1.timeout.connect(lambda: self.connection.write(f'b{lon1}'))
        self.timer1.start(3000)

        self.timer2 = QTimer()
        self.timer2.setSingleShot(True)  
        self.timer2.timeout.connect(lambda: self.connection.write(f'c{lat2}'))
        self.timer2.start(6000)

        self.timer3 = QTimer()
        self.timer3.setSingleShot(True)  
        self.timer3.timeout.connect(lambda: self.connection.write(f'd{lon2}'))
        self.timer3.start(9000)


    def showdata(self, data):
        print(data)

        if len(data) > 0 and data[0] == "<" and data[-1] == ">":
            data = data.strip("<>")
            values = data.split(",")

            self.view.set_speed(int(values[0]) * 4)
            self.view.set_spray(int(values[1]) * 5)


        elif len(data) > 0 and data[0] == '[' and data[-1] == ']':
            data = data.strip("[]")
            values = data.split(",")
            if len(values[0]) > 6:
                self.lat, self.lon = values[0], values[1]
            self.view.set_position(self.lat, self.lon)


        elif len(data) > 0 and data[0] == '(' and data[-1] == ')':
            data = data.strip("()")
            values = data.split(",")

            self.view.add_log('Early blight', self.lat, self.lon, values[0], values[1], values[2], values[3], datetime.now().strftime("%H:%M"))

            self.view.add_data(self.lat, self.lon)

            self.plant_count += 1
            self.view.set_diseased_count(self.plant_count)

        
        elif len(data) > 0 and data[0] == '-' and data[-1] == '-':
            data = data.strip("--")
            values = data.split(",")
            self.view.set_battery(int(values[0]))
            temp = int(values[1])
            self.view.set_heading(self.get_heading(temp))

        elif len(data) > 0 and data[0] == '+' and data[-1] == '+':
            data = data.strip("++")
            values = data.split(",")
            self.view.set_grid(values[0], values[1], values[2], values[3], values[4])




    def convert_to_decimal(self, lat_str, lon_str):
        # Clean the input strings
        lat_str = lat_str.strip().replace("'", "").replace('"', "").replace(" ", "")
        lon_str = lon_str.strip().replace("'", "").replace('"', "").replace(" ", "")
        
        # Convert latitude
        lat_degrees = int(lat_str[:2])  # First 2 characters are degrees
        lat_minutes = float(lat_str[2:])  # Remaining characters are minutes
        latitude = lat_degrees + (lat_minutes / 60)

        # Convert longitude
        lon_degrees = int(lon_str[:3])  # First 3 characters are degrees
        lon_minutes = float(lon_str[3:])  # Remaining characters are minutes
        longitude = lon_degrees + (lon_minutes / 60)

        latitude = round(latitude, 6)
        longitude = round(longitude, 6)

        return latitude, longitude

    
    
        
    def get_heading(self, angle):
        if (angle >= 338 or angle < 22):
            return 0
        elif (angle >= 22 and angle < 67):
            return 45
        elif (angle >= 67 and angle < 112):
            return 90
        elif (angle >= 112 and angle < 157):
            return 135
        elif (angle >= 157 and angle < 202):
            return 180
        elif (angle >= 202 and angle < 247):
            return 225
        elif (angle >= 247 and angle < 292):
            return 270
        elif (angle >= 292 and angle < 338):
            return 315




        



    def reciever_status(self, state):
        self.view.connection_status(state)
        

    def test(self,str):
        print(str)

    def test3(self):
       print('here')
       self.view.add_data(23.7978814, 90.4499017)

    def test2(self,lat, lon, lat1, lon2):
        print(f'{lat}, {lon}, {lat1}, {lon2}')

    def process_log_suggestion(self, n, p, k, water, disease, lat, lon):
        self.view.set_log_suggestion("Loading........")
        self.worker = MyWorker(self.ai, n, p, k, water, disease)
        self.worker.done.connect(self.result) 
        self.worker.start() 

    def process_area_suggestion(self, n, p ,k ,water):
        self.view.set_log_suggestion("Loading........")
        self.worker = MyWorker_2(self.ai, n, p, k, water)
        self.worker.done.connect(self.result_2) 
        self.worker.start()

 

    def result(self, dataa):
        self.view.set_log_suggestion(dataa)

    def result_2(self, dataa):
        self.view.set_log_suggestion(dataa)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    exit(app.exec())
