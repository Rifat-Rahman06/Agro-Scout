import RPi.GPIO as GPIO
import gy73
import math
import os
import serial
import smbus
import time
import cv2
import numpy as np

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    try:
        from tensorflow.lite import Interpreter
    except ImportError:
        raise ImportError("Install tflite-runtime (or tensorflow) to run the models")


class agro_nest:
    def __init__(self):

        self.camera_angel = -1
        self.rotation_delay = 0.01
        self.move_camera(90)

        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

        self.leaf_detect = Interpreter(os.path.join(model_dir, "leaf_detect.tflite"))
        self.leaf_detect.allocate_tensors()
        detect_details = self.leaf_detect.get_input_details()[0]
        self.leaf_detect_input_index = detect_details["index"]
        self.leaf_detect_input_shape = detect_details["shape"]
        self.leaf_detect_output_index = self.leaf_detect.get_output_details()[0]["index"]

        self.leaf_classify = Interpreter(os.path.join(model_dir, "leaf_classify.tflite"))
        self.leaf_classify.allocate_tensors()
        classify_details = self.leaf_classify.get_input_details()[0]
        self.leaf_classify_input_index = classify_details["index"]
        self.leaf_classify_input_shape = classify_details["shape"]
        self.leaf_classify_output_index = self.leaf_classify.get_output_details()[0]["index"]

        # GPS serial (NEO-8M on Pi GPIO 15 / UART RX)
        # NOTE: Disable Pi serial console first:
        #   sudo raspi-config -> Interface Options -> Serial -> No
        try:
            self.gps_serial = serial.Serial("/dev/serial0", 9600, timeout=0.5)
        except:
            self.gps_serial = None

    def angle_to_duty_cycle(self, angle):
        return 2.5 + (angle / 18.0)

    def drop(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(5, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)

        servo1 = GPIO.PWM(5, 50)
        servo2 = GPIO.PWM(6, 50)

        servo1_angle = 10
        servo2_angle = 165
        servo1.start(self.angle_to_duty_cycle(servo1_angle))
        servo2.start(self.angle_to_duty_cycle(servo2_angle))
        time.sleep(1)

        delay = 0.01

        try:
            for i in range(1, 94):
                servo1_angle += 1
                servo2_angle -= 1
                servo1.ChangeDutyCycle(self.angle_to_duty_cycle(servo1_angle))
                servo2.ChangeDutyCycle(self.angle_to_duty_cycle(servo2_angle))
                time.sleep(delay)

            time.sleep(0.5)

            for i in range(1, 94):
                servo1_angle -= 1
                servo2_angle += 1
                servo1.ChangeDutyCycle(self.angle_to_duty_cycle(servo1_angle))
                servo2.ChangeDutyCycle(self.angle_to_duty_cycle(servo2_angle))
                time.sleep(delay)

        finally:
            servo1.stop()
            servo2.stop()
            GPIO.cleanup()

    def buzzer(self, interval):

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(16, GPIO.OUT)
        GPIO.output(16, GPIO.HIGH)
        time.sleep(interval)
        GPIO.output(16, GPIO.LOW)
        GPIO.cleanup()

    def pump(self, interval):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(22, GPIO.OUT)
        GPIO.output(22, GPIO.HIGH)
        time.sleep(interval)
        GPIO.output(22, GPIO.LOW)
        GPIO.cleanup()

    def move_camera(self, rotation):
        GPIO.setmode(GPIO.BCM)
        servo_pin = 17
        GPIO.setup(servo_pin, GPIO.OUT)
        pwm = GPIO.PWM(servo_pin, 50)

        pwm.start(0)

        if self.camera_angel == -1:
            pwm.ChangeDutyCycle(self.angle_to_duty_cycle(90))

        elif rotation < self.camera_angel:
            for i in range(self.camera_angel, rotation - 1, -1):
                pwm.ChangeDutyCycle(self.angle_to_duty_cycle(i))
                time.sleep(self.rotation_delay)

        elif rotation > self.camera_angel:
            for i in range(self.camera_angel, rotation + 1):
                pwm.ChangeDutyCycle(self.angle_to_duty_cycle(i))
                time.sleep(self.rotation_delay)

        self.camera_angel = rotation
        time.sleep(1)
        pwm.stop()
        GPIO.cleanup(servo_pin)

    def get_list(self, data):
        if "[" in data and "]" in data:
            data = data[data.index("[") + 1 : data.index("]")]
            data = data.split(",")
            return data
        else:
            return -1

    def npkw(self):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in "[N]"])
        time.sleep(5)
        data = bus.read_i2c_block_data(address, 0, 20)
        response = "".join([chr(i) for i in data]).strip()
        bus.close()
        del bus
        return self.get_list(response)

    def push(self):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in "[D]"])
        bus.close()
        del bus

    def pull(self):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in "[U]"])
        bus.close()
        del bus

    def set_running_interval(self, interval):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in f"[T,{interval}]"])
        bus.close()
        del bus

    def forward(self, speed):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in f"[F,{speed}]"])
        bus.close()
        del bus

    def backward(self, speed):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in f"[B,{speed}]"])
        bus.close()
        del bus

    def left(self, speed):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in f"[L,{speed}]"])
        bus.close()
        del bus

    def right(self, speed):
        bus = smbus.SMBus(1)
        address = 0x20
        bus.write_i2c_block_data(address, 0, [ord(c) for c in f"[R,{speed}]"])
        bus.close()
        del bus

    def sent(self, data):
        bus = smbus.SMBus(1)
        I2C_ADDRESS = 0x20
        bus.write_i2c_block_data(I2C_ADDRESS, 0, list(f"{data}".encode("utf-8")))
        bus.close()
        del bus

    def read_data(self):
        bus = smbus.SMBus(1)
        SLAVE_ADDRESS = 0x20
        data = bus.read_i2c_block_data(SLAVE_ADDRESS, 0, 32)
        data = "".join([chr(byte) for byte in data if byte != 0])
        bus.close()
        del bus
        return self.get_list(data)

    def read_gps(self):
        """Read GPS data from UART (NEO-8M on Pi GPIO 15). Returns [lat_str, lon_str] or [None, None]."""
        if self.gps_serial is None:
            return [None, None]
        for _ in range(10):
            line = self.gps_serial.readline().decode('ascii', errors='replace').strip()
            if line.startswith('$GPRMC'):
                parts = line.split(',')
                if len(parts) >= 7 and parts[3] and parts[5]:
                    return [parts[3], parts[5]]
        return [None, None]

    def read_sonar(self):
        """Read distance from HC-SR04 on GPIO 23/24. Returns distance in cm.
        NOTE: Use voltage divider on Echo pin (5V -> 3.3V for Pi safety):
            Sonar Echo -> 1kOhm -> GPIO 24
            GPIO 24 -> 2kOhm -> GND
        """
        TRIG = 23
        ECHO = 24
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)

        GPIO.output(TRIG, GPIO.LOW)
        time.sleep(0.002)
        GPIO.output(TRIG, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG, GPIO.LOW)

        # Wait for echo start
        start_time = time.time()
        while GPIO.input(ECHO) == 0:
            if time.time() - start_time > 0.05:
                return 999  # Timeout - no echo

        # Wait for echo end
        echo_start = time.time()
        while GPIO.input(ECHO) == 1:
            if time.time() - echo_start > 0.05:
                return 999  # Timeout - echo too long
        echo_end = time.time()

        distance = ((echo_end - echo_start) * 34300) / 2
        return distance

    def heading(self):
        bus = smbus.SMBus(1)
        bus.read_i2c_block_data(0x20, 0, 32)
        bus.close()
        del bus

        time.sleep(0.1)

        sensor = gy73.QMC5883L()
        mag_data = sensor.get_magnet()
        del sensor

        x = mag_data[0]
        y = mag_data[1]
        angle_rad = math.atan2(y, x)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360
        return int(angle_deg)

    def divide_rectangle(
        self,
        top_left_lat,
        top_left_lng,
        bottom_right_lat,
        bottom_right_lng,
        rows=10,
        cols=15,
    ):
        coordinates = []
        lat_step = (bottom_right_lat - top_left_lat) / (rows - 1)
        lng_step = (bottom_right_lng - top_left_lng) / (cols - 1)

        for i in range(rows):
            for j in range(cols):

                lat = top_left_lat + i * lat_step
                lng = top_left_lng + j * lng_step
                coordinates.append((lat, lng))
        return coordinates

    def min_distance(self, lat, lon, grid):
        min_dis = float("inf")
        closest_index = None

        for index, coord in enumerate(grid):

            dist = ((coord[0] - lat) ** 2 + (coord[1] - lon) ** 2) ** 0.5
            if dist < min_dis:
                min_dis = dist
                closest_index = index

        return closest_index

    def convert_to_decimal(self, lat_str, lon_str):
        lat_str = lat_str.strip().replace("'", "").replace('"', "").replace(" ", "")
        lon_str = lon_str.strip().replace("'", "").replace('"', "").replace(" ", "")
        lat_degrees = int(lat_str[:2])
        lat_minutes = float(lat_str[2:])
        latitude = lat_degrees + (lat_minutes / 60)

        # Convert longitude
        lon_degrees = int(lon_str[:3])
        lon_minutes = float(lon_str[3:])
        longitude = lon_degrees + (lon_minutes / 60)

        latitude = round(latitude, 6)
        longitude = round(longitude, 6)

        return latitude, longitude

    def initialize_camera(self, index=0):
        camera = cv2.VideoCapture(index)
        if not camera.isOpened():
            raise Exception("Error: Could not open camera.")
        return camera

    def letterbox(self, image, size):
        height, width = image.shape[:2]
        scale = min(size / width, size / height)
        new_width = int(round(width * scale))
        new_height = int(round(height * scale))
        resized = cv2.resize(image, (new_width, new_height))
        canvas = np.full((size, size, 3), 114, dtype=np.uint8)
        top = (size - new_height) // 2
        left = (size - new_width) // 2
        canvas[top:top + new_height, left:left + new_width] = resized
        return canvas, scale, left, top

    def nms(self, boxes, scores, iou_threshold=0.45):
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)
            if order.size == 1:
                break
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            width = np.maximum(0, xx2 - xx1 + 1)
            height = np.maximum(0, yy2 - yy1 + 1)
            intersection = width * height
            iou = intersection / (areas[i] + areas[order[1:]] - intersection)
            order = order[1:][iou <= iou_threshold]

        return keep

    def detect_leaves(self, image):

        size = int(self.leaf_detect_input_shape[1])
        padded, scale, left, top = self.letterbox(image, size)
        rgb_image = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)

        if len(self.leaf_detect_input_shape) == 4 and self.leaf_detect_input_shape[3] == 3:
            input_data = np.expand_dims(rgb_image, axis=0)
        else:
            input_data = np.expand_dims(rgb_image, axis=0).transpose(0, 3, 1, 2)

        input_data = (input_data.astype(np.float32) / 255.0)

        self.leaf_detect.set_tensor(self.leaf_detect_input_index, input_data)
        self.leaf_detect.invoke()
        output = np.squeeze(self.leaf_detect.get_tensor(self.leaf_detect_output_index))

        if output.ndim != 2:
            return []

        if output.shape[0] == 5:
            output = output.T

        scores = output[:, 4].astype(np.float32)
        if scores.max() > 1.0:
            scores = 1.0 / (1.0 + np.exp(-scores))

        mask = scores > 0.7
        if not mask.any():
            return []

        cx = (output[mask, 0] - left) / scale
        cy = (output[mask, 1] - top) / scale
        half_w = output[mask, 2] / (2 * scale)
        half_h = output[mask, 3] / (2 * scale)
        boxes = np.stack([cx - half_w, cy - half_h, cx + half_w, cy + half_h], axis=1)
        scores = scores[mask]

        keep = self.nms(boxes, scores)
        height, width = image.shape[:2]
        leaves = []

        for i in keep:
            x1 = max(0, int(boxes[i, 0]) - 10)
            x2 = min(width, int(boxes[i, 2]) + 10)
            y1 = max(0, int(boxes[i, 1]) - 10)
            y2 = min(height, int(boxes[i, 3]) + 10)
            leaves.append(image[y1:y2, x1:x2])

        return leaves

    def classify_leaves(self, leaves):

        size_h = int(self.leaf_classify_input_shape[1])
        size_w = int(self.leaf_classify_input_shape[2])
        predictions = []

        for cropped in leaves:
            resized_leaf = cv2.resize(cropped, (size_w, size_h))
            normalized_leaf = resized_leaf.astype(np.float32) / 255.0
            input_leaf = np.expand_dims(normalized_leaf, axis=0)
            self.leaf_classify.set_tensor(self.leaf_classify_input_index, input_leaf)
            self.leaf_classify.invoke()
            predictions.append(
                self.leaf_classify.get_tensor(self.leaf_classify_output_index)
            )

        return predictions

    def has_disease(self, predictions):

        for pred in predictions:
            if pred[0][1] > 0.7:
                return "1"

        return "0"

    def capture_and_classify_frame(self, camera):

        ret, frame = camera.read()
        if not ret:
            return "0"

        flipped_frame = cv2.flip(frame, 0)
        leaves = self.detect_leaves(flipped_frame)

        return self.has_disease(self.classify_leaves(leaves))

    def detect_path(self, image):

        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        lower_green = np.array([30, 30, 30])
        upper_green = np.array([100, 255, 255])

        green_mask = cv2.inRange(hsv_image, lower_green, upper_green)

        column_sum = np.sum(green_mask, axis=0)
        min_column = np.argmin(column_sum)

        height, width = image.shape[:2]

        bottom_center = (width // 2, height - 1)

        min_column_point = (min_column, 100)

        cv2.line(image, bottom_center, min_column_point, (0, 0, 255), 2)

        path_found = (column_sum[min_column] / height) < 0.5

        direction = ""
        degree = 0

        if bottom_center[0] < min_column_point[0]:
            direction = "right"
        else:
            direction = "left"

        delta_x = abs(min_column_point[0] - bottom_center[0])
        delta_y = abs(min_column_point[1] - bottom_center[1])
        degree = math.degrees(math.atan2(delta_y, delta_x))

        return direction, 90 - int(degree), path_found

    def capture_and_process_frame(self, camera):

        ret, frame = camera.read()
        if not ret:
            print("Error: Failed to capture frame.")
            return "left", 0, False

        flipped_frame = cv2.flip(frame, 0)

        direction, degree, path_found = self.detect_path(flipped_frame)

        return direction, degree, path_found

    def steer_to_path(self, direction, degree, speed, multiplier):

        if direction == "left":
            for i in range(int(multiplier * int(degree))):
                self.right(speed)
                time.sleep(0.1)
        else:
            for i in range(int(multiplier * int(degree))):
                self.left(speed)
                time.sleep(0.1)

    def search_path(self, camera, turn_steps=25):

        for turn_command in (self.left, self.right):
            for step in range(turn_steps):
                turn_command(50)
                time.sleep(0.05)
                direction, degree, path_found = self.capture_and_process_frame(camera)
                if path_found:
                    return direction, degree

        return None, None

    def is_within_rectangle(
        self,
        top_left_lat,
        top_left_lon,
        bottom_right_lat,
        bottom_right_lon,
        random_lat,
        random_lon,
    ):

        top_left_lat = float(top_left_lat)
        top_left_lon = float(top_left_lon)
        bottom_right_lat = float(bottom_right_lat)
        bottom_right_lon = float(bottom_right_lon)
        random_lat = float(random_lat)
        random_lon = float(random_lon)

        if (top_left_lat >= random_lat >= bottom_right_lat) and (
            top_left_lon <= random_lon <= bottom_right_lon
        ):
            print("Here - The point is within the rectangle")
            return True

        print("The point is outside the rectangle")
        return False


if __name__ == "__main__":
    ag = agro_nest()
    multiplier = 0.5
    auto_forward_go = 10
    camera = ag.initialize_camera(0)
    ag.buzzer(0.1)
    grid = None
    auto_rover_speed = 70
    rover_speed = 20
    spray_speed = 0.5
    battery = 0
    heading = 0
    lat1 = ""
    lon1 = ""
    lat2 = ""
    lon2 = ""
    lat = "23.7978814"
    lon = "90.4499017"
    field_iteration = 1
    autonomous = False
    failed_search = 0
    recovery_fails = 0
    previous_time = time.time()

    while True:
        data = ag.read_data()
        try:
            while autonomous and ag.is_within_rectangle(
                float(lat1), float(lon1), float(lat2), float(lon2), lat, lon
            ):
                if field_iteration % 3 == 0:
                    ag.push()
                    time.sleep(0.2)
                    field_data = ag.npkw()
                    time.sleep(0.2)
                    ag.pull()
                    index_of_part = ag.min_distance(float(lat), float(lon), grid)
                    ag.sent(
                        f"+{index_of_part},{field_data[0]},{field_data[1]},{field_data[2]},{field_data[3]}+"
                    )
                    time.sleep(0.5)

                direction, degree, path_found = ag.capture_and_process_frame(camera)

                if not path_found:
                    direction, degree = ag.search_path(camera)
                    if not direction:
                        failed_search += 1
                        ag.buzzer(0.3)
                        if failed_search >= 3:
                            ag.buzzer(0.5)
                            lat1 = ""
                            lon1 = ""
                            lat2 = ""
                            lon2 = ""
                            autonomous = False
                            grid = None
                            failed_search = 0
                            ag.move_camera(90)
                            break
                        continue

                failed_search = 0
                ag.steer_to_path(direction, degree, auto_rover_speed, multiplier)

                time.sleep(1)

                temp = ag.read_data()
                if temp[0] == "x":
                    ag.buzzer(0.4)
                    lat1 = ""
                    lon1 = ""
                    lat2 = ""
                    lon2 = ""
                    autonomous = False
                    grid = None
                    ag.move_camera(90)
                    break
                time.sleep(0.3)

                for i in range(auto_forward_go):
                    ag.forward(auto_rover_speed)
                    time.sleep(0.1)

                time.sleep(1)

                ag.move_camera(0)
                time.sleep(1)
                class_index = ag.capture_and_classify_frame(camera)
                time.sleep(0.3)
                temp = ag.read_data()
                if temp[0] == "x":
                    ag.buzzer(0.4)
                    lat1 = ""
                    lon1 = ""
                    lat2 = ""
                    lon2 = ""
                    autonomous = False
                    grid = None
                    ag.move_camera(90)
                    break
                time.sleep(0.3)

                print(class_index)

                if class_index != "0":
                    for i in range(15):
                        ag.buzzer(0.05)
                        time.sleep(0.05)

                    time.sleep(0.5)
                    ag.drop()
                    time.sleep(0.5)
                    ag.pump(spray_speed)

                    ag.push()
                    time.sleep(0.5)
                    
                    npkw_values = ag.npkw()
                    time.sleep(0.5)

                    ag.pull()
                    time.sleep(0.5)


                    ag.sent(
                        f"({npkw_values[0]}, {npkw_values[1]}, {npkw_values[2]}, {npkw_values[3]}, {class_index})"
                    )
                    time.sleep(0.3)

                temp = ag.read_data()
                if temp[0] == "x":
                    ag.buzzer(0.4)
                    lat1 = ""
                    lon1 = ""
                    lat2 = ""
                    lon2 = ""
                    autonomous = False
                    grid = None
                    ag.move_camera(90)
                    break
                time.sleep(0.3)

                ag.move_camera(180)
                time.sleep(1)
                class_index = ag.capture_and_classify_frame(camera)

                time.sleep(0.3)
                temp = ag.read_data()
                if temp[0] == "x":
                    ag.buzzer(0.4)
                    lat1 = ""
                    lon1 = ""
                    lat2 = ""
                    lon2 = ""
                    autonomous = False
                    grid = None
                    ag.move_camera(90)
                    break
                time.sleep(0.3)

                print(class_index)

                if class_index != "0":
                    for i in range(15):
                        ag.buzzer(0.05)
                        time.sleep(0.05)

                    time.sleep(0.5)
                    ag.drop()
                    time.sleep(0.5)
                    ag.pump(spray_speed)

                    ag.push()
                    time.sleep(0.5)

                    npkw_values = ag.npkw()
                    time.sleep(0.5)

                    ag.pull()
                    time.sleep(0.5)

                    ag.sent(
                        f"({npkw_values[0]}, {npkw_values[1]}, {npkw_values[2]}, {npkw_values[3]}, {class_index})"
                    )
                    time.sleep(0.5)

                read_value = ag.read_data()
                battery = int((int(read_value[2]) / 2300) * 100)
                time.sleep(0.1)
                heading = ag.heading()
                time.sleep(0.3)
                ag.sent(f"-{battery},{heading}-")
                time.sleep(0.3)

                gps_data = ag.read_gps()
                if gps_data[0]:
                    lat, lon = ag.convert_to_decimal(gps_data[0], gps_data[1])
                    time.sleep(0.1)

                ag.sent(f"[{lat}, {lon}]")

                time.sleep(0.3)

                ag.move_camera(90)
                if read_value[0] == "x":
                    ag.buzzer(0.4)
                    lat1 = ""
                    lon1 = ""
                    lat2 = ""
                    lon2 = ""
                    autonomous = False
                    grid = None
                    ag.move_camera(90)
                    break

                time.sleep(0.5)
                field_iteration += 1

            if lat1 and lon1 and lat2 and lon2:
                if grid is None:
                    grid = ag.divide_rectangle(
                        float(lat1), float(lon1), float(lat2), float(lon2)
                    )
                autonomous = True

                if not ag.is_within_rectangle(
                    float(lat1), float(lon1), float(lat2), float(lon2), lat, lon
                ):
                    direction, degree = ag.search_path(camera)
                    if direction:
                        ag.steer_to_path(direction, degree, auto_rover_speed, multiplier)
                        for i in range(auto_forward_go):
                            ag.forward(auto_rover_speed)
                            time.sleep(0.1)
                        gps_data = ag.read_gps()
                        time.sleep(0.1)
                        if gps_data[0]:
                            lat, lon = ag.convert_to_decimal(gps_data[0], gps_data[1])
                        time.sleep(0.2)
                        if ag.is_within_rectangle(
                            float(lat1), float(lon1), float(lat2), float(lon2), lat, lon
                        ):
                            recovery_fails = 0
                        else:
                            recovery_fails += 1
                    else:
                        recovery_fails += 1
                        ag.buzzer(0.3)

                    if recovery_fails >= 4:
                        ag.buzzer(0.5)
                        lat1 = ""
                        lon1 = ""
                        lat2 = ""
                        lon2 = ""
                        autonomous = False
                        grid = None
                        recovery_fails = 0
                        ag.move_camera(90)

            if data[0] == "F" and ag.read_sonar() > 45:
                ag.forward(rover_speed)
                previous_time = time.time()

            elif data[0] == "B":
                ag.backward(rover_speed)
                previous_time = time.time()

            elif data[0] == "L":
                ag.left(rover_speed + 100)
                previous_time = time.time()

            elif data[0] == "R":
                ag.right(rover_speed + 100)
                previous_time = time.time()

            elif data[0] == "d":
                ag.buzzer(0.2)
                direction, degree, path_found = ag.capture_and_process_frame(camera)

                if not path_found:
                    direction, degree = ag.search_path(camera)
                    if not direction:
                        ag.buzzer(0.3)
                        continue

                ag.steer_to_path(direction, degree, auto_rover_speed, multiplier)

                time.sleep(1)

                for i in range(auto_forward_go):
                    ag.forward(auto_rover_speed)
                    time.sleep(0.1)

                time.sleep(1)

                ag.move_camera(0)
                time.sleep(1)
                class_index = ag.capture_and_classify_frame(camera)
                time.sleep(0.3)

                print(class_index)

                if class_index != "0":
                    for i in range(15):
                        ag.buzzer(0.05)
                        time.sleep(0.05)

                    time.sleep(0.5)
                    ag.drop()
                    time.sleep(0.5)
                    ag.pump(spray_speed)

                    ag.push()
                    time.sleep(0.5)

                    npkw_values = ag.npkw()
                    time.sleep(0.5)

                    ag.pull()
                    time.sleep(0.5)

                    ag.sent(
                        f"({npkw_values[0]}, {npkw_values[1]}, {npkw_values[2]}, {npkw_values[3]}, {class_index})"
                    )
                    time.sleep(0.5)

                ag.move_camera(180)
                time.sleep(1)
                class_index = ag.capture_and_classify_frame(camera)

                time.sleep(0.3)

                print(class_index)

                if class_index != "0":
                    for i in range(15):
                        ag.buzzer(0.05)
                        time.sleep(0.05)

                    time.sleep(0.5)
                    ag.drop()
                    time.sleep(0.5)
                    ag.pump(spray_speed)

                    ag.push()
                    time.sleep(0.5)

                    npkw_values = ag.npkw()
                    time.sleep(0.5)

                    ag.pull()
                    time.sleep(0.5)

                    ag.sent(
                        f"({npkw_values[0]}, {npkw_values[1]}, {npkw_values[2]}, {npkw_values[3]}, {class_index})"
                    )
                    time.sleep(0.5)


                ag.move_camera(90)

                time.sleep(0.5)
                

            elif data[0] != "":
                temp = data[0]

                if temp[0] == "s":
                    rover_speed = int(temp[1:]) * 3
                elif temp[0] == "g":
                    spray_speed = int(temp[1:]) / 10
                elif temp[0] == "a":
                    lat1 = temp[1:]
                    previous_time = time.time()
                    ag.buzzer(0.2)
                    print(lat1)
                elif temp[0] == "b":
                    lon1 = temp[1:]
                    previous_time = time.time()
                    ag.buzzer(0.3)
                    print(lon1)
                elif temp[0] == "c":
                    lat2 = temp[1:]
                    previous_time = time.time()
                    ag.buzzer(0.3)
                    print(lat2)
                elif temp[0] == "d":
                    lon2 = temp[1:]
                    previous_time = time.time()
                    ag.buzzer(0.3)
                    print(lon2)
                elif temp[0] == "x":
                    ag.buzzer(0.4)
                    lat1 = ""
                    lon1 = ""
                    lat2 = ""
                    lon2 = ""
                    autonomous = False
                    grid = None

            elif (time.time() - previous_time) >= 3:
                battery = int((int(data[2]) / 2300) * 100)
                heading = int(ag.heading())
                heading += 112
                heading = heading % 360

                ag.sent(f"-{battery},{heading}-")
                time.sleep(0.2)
                gps_data = ag.read_gps()
                time.sleep(0.1)
                if gps_data[0]:
                    lat, lon = ag.convert_to_decimal(gps_data[0], gps_data[1])
                ag.sent(f"[{lat}, {lon}]")
                time.sleep(0.2)
                previous_time = time.time()

        except:
            print("Error fetcing data")
        time.sleep(0.07)
