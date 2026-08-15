import serial, time
import serial.tools.list_ports
from PySide6.QtCore import Signal, QObject, QThread, QMutex, QMutexLocker

class connection(QObject):
    active = Signal(bool)
    has_data = Signal(str)

    def __init__(self, vid, pid, baud_rate):
        super().__init__()

        self.available = False
        self.data_in = False
        self.data_to_write = ''
        self.vid = vid
        self.pid = pid
        self.serial_port = ''
        self.baud_rate = baud_rate

        self.last_check_time = time.time()
        self.check_interval = 2

        self.mutex = QMutex()

        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.operation)
        self.thread.start()

    def write(self, data):
        with QMutexLocker(self.mutex):
            self.data_to_write = data
            self.data_in = False

    def operation(self):
        ser = None
        establish = False

        while True:
            current_time = time.time()

            if current_time - self.last_check_time >= self.check_interval:
                self.last_check_time = current_time

                ports = serial.tools.list_ports.comports()
                device_found = False

                for port in ports:
                    if port.vid == self.vid and port.pid == self.pid:
                        self.serial_port = port.device
                        device_found = True
                        break

                with QMutexLocker(self.mutex):
                    if device_found and not self.available:
                        self.available = True
                        self.active.emit(True)
                    elif not device_found and self.available:
                        self.serial_port = ''
                        self.available = False
                        self.active.emit(False)

            if self.available and not establish:
                try:
                    ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                    self.data_in = True
                    establish = True
                except:
                    print("Can't establish a connection")
                    self.last_check_time -= 2
                    continue

            elif self.available and establish:
                try:
                    with QMutexLocker(self.mutex):
                        if self.data_in:
                            if ser.in_waiting > 0:
                                response = ser.readline().decode().strip()
                                self.has_data.emit(response)
                        else:
                            ser.write(self.data_to_write.encode())
                            self.data_in = True
                except:
                    self.data_in = True
                    self.last_check_time -= 2

            elif not self.available and establish:
                if ser:
                    ser.close()
                ser = None
                establish = False
