#include <Arduino.h>
#include <Wire.h>
#include <LoRa.h>
#include <SPI.h>
#include <ESP32Servo.h>

#define SLAVE_ADDRESS 0x20

// ===== FINAL PIN DEFINITIONS =====

// --- LoRa SX1278 ---
// SPI bus: SCK=18, MISO=19, MOSI=23 (VSPI default)
// NSS/CS on GPIO 17 (moved from 18 to free SCK)
#define LORA_NSS 17
#define LORA_RST 5      // WARNING: GPIO 5 is an ESP32 strapping pin.
                         // Add 10kΩ pull-up to VCC to ensure HIGH during boot.
#define LORA_DIO0 15    // WARNING: GPIO 15 is an ESP32 strapping pin.
                         // Ensure SX1278 DIO0 is LOW during ESP32 boot; add 10kΩ puls-
                         // down to GND if needed.

// --- I2C (to Raspberry Pi) ---
#define I2C_SDA 21
#define I2C_SCL 22

// --- Motor Control (BTS7960) ---
// EN pins hardwired to VCC (always enabled) - no GPIO needed
// L_EN and R_EN removed: tie to 3.3V on PCB
#define L_RPWM 4    // Left motor reverse PWM
#define L_LPWM 13   // Left motor forward PWM
#define R_RPWM 14   // Right motor reverse PWM
#define R_LPWM 16   // Right motor forward PWM

// --- RS485 / Modbus (NPK sensor) ---
#define MODBUS_RX 25
#define MODBUS_TX 26
#define MODBUS_BAUD 4800
#define RS485_REDE 27   // Combined RE + DE direction control

// --- NPK Servo ---
#define SERVO_PIN 33

// --- Soil Moisture ---
#define MOISTURE_PIN 32

// --- Battery Monitor ---
#define VOLTAGE_PIN 35  // Input-only on ESP32

// Modbus RTU requests (NPK sensor)
const byte nitro[] = { 0x01, 0x03, 0x00, 0x1e, 0x00, 0x01, 0xe4, 0x0c };
const byte phos[] = { 0x01, 0x03, 0x00, 0x1f, 0x00, 0x01, 0xb5, 0xcc };
const byte pota[] = { 0x01, 0x03, 0x00, 0x20, 0x00, 0x01, 0x85, 0xc0 };

// ===== STORE VARIABLES =====
String data = "";
bool data_ready = false;
String data_sent = "";
int vol = 0;

// NPK / motor variables
int run_time = 100;
bool running = false;
bool isnpk = false;
bool npk_ready = false;
int n_val = 0;
int p_val = 0;
int k_val = 0;
float moisture_val = 0.0;

byte values[11];
ESP32Servo npk_servo;

// I2C response mode tracking
enum ResponseMode { MODE_DEFAULT, MODE_NPK };
ResponseMode response_mode = MODE_DEFAULT;

// Pending motor command (set in receiveEvent ISR, executed in motor_task)
volatile char motor_cmd = 0;
volatile int motor_speed = 0;

// ===== SEMAPHORES =====
SemaphoreHandle_t data_mutex;
SemaphoreHandle_t data_ready_mutex;
SemaphoreHandle_t data_sent_mutex;
SemaphoreHandle_t vol_mutex;
SemaphoreHandle_t npk_mutex;

// ===== TASK HANDLES =====
TaskHandle_t lora_data = NULL;
TaskHandle_t modbus_data = NULL;
TaskHandle_t motor_data = NULL;

// ===== FUNCTION PROTOTYPES =====
void lora_task(void *pvParameters);
void modbus_task(void *pvParameters);
void motor_task(void *pvParameters);
void receiveEvent(int numBytes);
void requestEvent();

// Motor / NPK functions
void forward(int speed);
void backward(int speed);
void right(int speed);
void left(int speed);
void stop();
int readValue(const byte *request);
float moisture();
void push();
void pull();

void setup() {
  // I2C slave at 0x20
  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);

  // Modbus UART2 (replaces Arduino SoftwareSerial)
  Serial2.begin(MODBUS_BAUD, SERIAL_8N1, MODBUS_RX, MODBUS_TX);

  // Spi.begin with explicit pins; SS=-1 avoids conflict with GPIO 5 (LoRa RST)
  SPI.begin(18, 19, 23, -1);  // SCK=18, MISO=19, MOSI=23, SS=disabled

  // LoRa (pins: NSS=17, RST=5, DIO0=15)
  LoRa.setPins(LORA_NSS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) {
    delay(1000);
    if (!LoRa.begin(433E6)) {
      while (1);
    }
  }
  delay(2000);

  // Motor pins (EN pins hardwired to VCC, not controlled by GPIO)
  pinMode(L_RPWM, OUTPUT);
  pinMode(L_LPWM, OUTPUT);
  pinMode(R_RPWM, OUTPUT);
  pinMode(R_LPWM, OUTPUT);
  pinMode(SERVO_PIN, OUTPUT);

  // Set RS485 direction control to receive (LOW)
  pinMode(RS485_REDE, OUTPUT);
  digitalWrite(RS485_REDE, LOW);

  delay(500);

  // Battery + moisture pins
  pinMode(VOLTAGE_PIN, INPUT);
  pinMode(MOISTURE_PIN, INPUT);

  // Servo init
  npk_servo.attach(SERVO_PIN, 500, 2500);
  npk_servo.write(0);
  unsigned long startTime = millis();
  while (millis() - startTime < 2000) {
    delay(20);
  }
  delay(1000);

  // Create semaphores
  data_mutex = xSemaphoreCreateMutex();
  data_ready_mutex = xSemaphoreCreateMutex();
  data_sent_mutex = xSemaphoreCreateMutex();
  vol_mutex = xSemaphoreCreateMutex();
  npk_mutex = xSemaphoreCreateMutex();

  // Create tasks (no GPS or sonar tasks - moved to Pi)
  xTaskCreatePinnedToCore(lora_task, "LoRa Task", 4096, NULL, 1, &lora_data, 1);
  xTaskCreatePinnedToCore(modbus_task, "Modbus Task", 4096, NULL, 1, &modbus_data, 0);
  xTaskCreatePinnedToCore(motor_task, "Motor Task", 4096, NULL, 1, &motor_data, 0);
}

void loop() {
  vTaskDelay(portMAX_DELAY);
}

// ===== I2C COMMUNICATION =====
void receiveEvent(int numBytes) {
  String str = "";
  while (Wire.available()) {
    char c = Wire.read();
    str += c;
  }
  str = str.substring(1);  // Remove register byte from smbus protocol

  // Check for motor/operation commands (start with '[')
  if (str.length() > 0 && str[0] == '[') {
    char command = str[1];
    int value = 0;
    if (str.length() > 3 && str.charAt(2) == ',') {
      value = str.substring(3, str.length() - 1).toInt();
    }

    // Recognized motor/operation commands
    if (command == 'F' || command == 'B' || command == 'L' || command == 'R' ||
        command == 'T' || command == 'D' || command == 'U' || command == 'N') {
      switch (command) {
        case 'F':
          motor_cmd = 'F';
          motor_speed = value > 0 ? value : 70;
          response_mode = MODE_DEFAULT;
          break;
        case 'B':
          motor_cmd = 'B';
          motor_speed = value > 0 ? value : 70;
          response_mode = MODE_DEFAULT;
          break;
        case 'L':
          motor_cmd = 'L';
          motor_speed = value > 0 ? value : 100;
          response_mode = MODE_DEFAULT;
          break;
        case 'R':
          motor_cmd = 'R';
          motor_speed = value > 0 ? value : 100;
          response_mode = MODE_DEFAULT;
          break;
        case 'T':
          run_time = value > 0 ? value : run_time;
          response_mode = MODE_DEFAULT;
          break;
        case 'D':
          motor_cmd = 'D';
          response_mode = MODE_DEFAULT;
          break;
        case 'U':
          motor_cmd = 'U';
          response_mode = MODE_DEFAULT;
          break;
        case 'N':
          isnpk = true;
          response_mode = MODE_NPK;
          break;
      }
    } else {
      // Not a recognized motor command, forward as data via LoRa
      xSemaphoreTake(data_sent_mutex, portMAX_DELAY);
      data_sent = str;
      xSemaphoreGive(data_sent_mutex);
    }
  } else {
    // Data to forward via LoRa (e.g., autonomous mode coordinates, battery/heading data)
    xSemaphoreTake(data_sent_mutex, portMAX_DELAY);
    data_sent = str;
    xSemaphoreGive(data_sent_mutex);
  }
}

void requestEvent() {
  String temp = "[";

  if (response_mode == MODE_NPK && npk_ready) {
    if (xSemaphoreTake(npk_mutex, portMAX_DELAY) == pdTRUE) {
      temp += String(n_val) + ',' + String(p_val) + ',' + String(k_val) + ',' + String((int)moisture_val);
      xSemaphoreGive(npk_mutex);
    }
    npk_ready = false;
  }
  else {
    // Default: LoRa data + obstacle placeholder (0 = no obstacle, sonar moved to Pi) + battery voltage
    if (xSemaphoreTake(data_ready_mutex, portMAX_DELAY) == pdTRUE) {
      if (data_ready == true) {
        if (xSemaphoreTake(data_mutex, portMAX_DELAY) == pdTRUE) {
          temp += data;
          xSemaphoreGive(data_mutex);
        }
        data_ready = false;
      }
      temp += ',';
      xSemaphoreGive(data_ready_mutex);
    }
    temp += '0';   // Obstacle = always 0 (sonar moved to Pi)
    temp += ',';
    if (xSemaphoreTake(vol_mutex, portMAX_DELAY) == pdTRUE) {
      temp += String(vol);
      xSemaphoreGive(vol_mutex);
    }
  }

  temp += ']';
  for (int i = 0; i < temp.length(); i++) {
    Wire.write((uint8_t)temp[i]);
  }
}

// ===== LORA TASK (receives from remote, forwards data to remote) =====
void lora_task(void *pvParameters) {
  while (true) {
    int packetSize = LoRa.parsePacket();
    if (packetSize) {
      while (LoRa.available()) {
        String packet = LoRa.readString();

        if (xSemaphoreTake(data_mutex, portMAX_DELAY) == pdTRUE) {
          data = packet;
          xSemaphoreGive(data_mutex);
        }
        if (xSemaphoreTake(data_ready_mutex, portMAX_DELAY) == pdTRUE) {
          data_ready = true;
          xSemaphoreGive(data_ready_mutex);
        }
      }
    }
    // Forward data sent from Pi to remote via LoRa
    if (xSemaphoreTake(data_sent_mutex, portMAX_DELAY) == pdTRUE) {
      if (!data_sent.isEmpty()) {
        LoRa.beginPacket();
        LoRa.print(data_sent);
        LoRa.endPacket();
      }
      data_sent = "";
      xSemaphoreGive(data_sent_mutex);
    }
    vTaskDelay(1 / portTICK_PERIOD_MS);
  }
}

// ===== MODBUS TASK (NPK sensor reading via UART2 + RS485) =====
void modbus_task(void *pvParameters) {
  while (true) {
    if (isnpk) {
      n_val = readValue(nitro);
      delay(100);
      p_val = readValue(phos);
      delay(100);
      k_val = readValue(pota);
      delay(500);

      // Read moisture sensor
      moisture_val = moisture();

      npk_ready = true;
      isnpk = false;
    }
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}

// ===== MOTOR TASK (executes commands from I2C, handles motor timing) =====
void motor_task(void *pvParameters) {
  while (true) {
    // Execute pending motor command (set by receiveEvent ISR)
    if (motor_cmd != 0) {
      switch (motor_cmd) {
        case 'F': forward(motor_speed); break;
        case 'B': backward(motor_speed); break;
        case 'L': left(motor_speed); break;
        case 'R': right(motor_speed); break;
        case 'D': push(); break;
        case 'U': pull(); break;
      }
      motor_cmd = 0;
    }

    // Handle auto-stop after run_time
    if (running && millis() - start_time >= run_time) {
      stop();
      running = false;
    }

    // Sample + average battery ADC over ~1 s (100 x 10ms), publish to requestEvent
    static int vol_count = 0;
    static long vol_sum = 0;
    vol_sum += analogRead(VOLTAGE_PIN);
    if (++vol_count >= 100) {
      if (xSemaphoreTake(vol_mutex, portMAX_DELAY) == pdTRUE) {
        vol = (int)(vol_sum / vol_count);
        xSemaphoreGive(vol_mutex);
      }
      vol_sum = 0;
      vol_count = 0;
    }

    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

// ===== MOTOR / CONTROL FUNCTIONS =====
void forward(int speed) {
  start_time = millis();
  running = true;

  // EN pins hardwired to VCC - no digitalWrite needed
  analogWrite(L_LPWM, 0);
  analogWrite(R_LPWM, 0);
  analogWrite(L_RPWM, speed);
  analogWrite(R_RPWM, speed);
}

void backward(int speed) {
  start_time = millis();
  running = true;

  analogWrite(L_RPWM, 0);
  analogWrite(R_RPWM, 0);
  analogWrite(L_LPWM, speed);
  analogWrite(R_LPWM, speed);
}

void right(int speed) {
  start_time = millis();
  running = true;

  analogWrite(L_RPWM, 0);
  analogWrite(R_LPWM, 0);
  analogWrite(L_LPWM, speed);
  analogWrite(R_RPWM, speed);
}

void left(int speed) {
  start_time = millis();
  running = true;

  analogWrite(L_LPWM, 0);
  analogWrite(R_RPWM, 0);
  analogWrite(L_RPWM, speed);
  analogWrite(R_LPWM, speed);
}

void stop() {
  analogWrite(L_LPWM, 0);
  analogWrite(L_RPWM, 0);
  analogWrite(R_LPWM, 0);
  analogWrite(R_RPWM, 0);
  // EN pins hardwired to VCC - no digitalWrite needed
}

int readValue(const byte *request) {
  // Set RS485 module to transmit mode
  digitalWrite(RS485_REDE, HIGH);

  // Send Modbus RTU request
  for (byte i = 0; i < 8; i++) {
    Serial2.write(request[i]);
  }
  Serial2.flush();

  // Set RS485 module to receive mode
  digitalWrite(RS485_REDE, LOW);

  // Wait for response
  delay(500);

  byte responseLength = Serial2.available();
  if (responseLength == 0) {
    return -1;
  }

  for (byte i = 0; i < responseLength; i++) {
    values[i] = Serial2.read();
  }

  if (responseLength < 5) {
    return -1;
  }

  return (values[3] << 8 | values[4]);
}

float moisture() {
  float moisture_percentage;
  int sensor_analog;
  sensor_analog = analogRead(MOISTURE_PIN);
  moisture_percentage = map(sensor_analog, 0, 4095, 100, 0);
  return moisture_percentage;
}

void push() {
  for (int angle = 0; angle <= 220; angle++) {
    npk_servo.write(angle);
    delay(5);
  }
}

void pull() {
  for (int angle = 220; angle >= 0; angle--) {
    npk_servo.write(angle);
    delay(5);
  }
}
