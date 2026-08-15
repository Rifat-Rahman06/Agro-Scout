#include <LoRa.h>

const int pot1Pin = 34;       // Potentiometer 1 (Analog)
const int pot2Pin = 35;       // Potentiometer 2 (Analog)
const int joyXPin = 32;       // Joystick X-axis (Analog)
const int joyYPin = 33;       // Joystick Y-axis (Analog)
const int joySwitchPin = 25;  // Joystick switch (Digital Interrupt)

const int buzzerPin = 26;     // Buzzer
const int redLEDPin = 13;     // Red LED
const int greenLEDPin = 12;   // Green LED
const int blueLEDPin = 14;    // Blue LED

unsigned long startmillis;

int pot1Value = 0;
int pot2Value = 0;
int joyXValue = 0;
int joyYValue = 0;
char joystick = '0';
volatile bool joySwitchPressed = false; 
bool pot1Value_change = false;
bool pot2Value_change = false;
unsigned long speed_time = 0;
unsigned long beacon_time = 0;
bool beacon_state = false;
int count = 80;

unsigned long lastJoySwitchPress = 0;  // Timestamp of last button press
const unsigned long debounceDelay = 50; // Debounce time in milliseconds
bool lastButtonState = HIGH; // Track the last state of the button

void IRAM_ATTR handleJoySwitch() {
  // Check if enough time has passed since the last press
  if (millis() - lastJoySwitchPress > debounceDelay) {
    joySwitchPressed = true;  
    lastJoySwitchPress = millis(); // Update the timestamp of the last press
  }
}

void readSensor() {
  joyXValue = analogRead(joyXPin);
  joyYValue = analogRead(joyYPin);

  char temp = '0';

  if (joyXValue > 3000)
    temp = 'F';
  if (joyXValue < 1000)
    temp = 'B';
  if (joyYValue > 3000) 
    temp = 'R';
  if (joyYValue < 1000) 
    temp = 'L';
  
  joystick = temp;

  int temp_pot1Value = analogRead(pot1Pin);
  temp_pot1Value = map(temp_pot1Value, 0, 4096, 0, 25);
  if (temp_pot1Value != pot1Value) {
    pot1Value = temp_pot1Value;
    pot1Value_change = true;
  }

  int temp_pot2Value = analogRead(pot2Pin);
  temp_pot2Value = map(temp_pot2Value, 0, 4096, 1, 63);
  if (temp_pot2Value != pot2Value) {
    pot2Value = temp_pot2Value;
    pot2Value_change = true;
  }

}

void setup() {
  Serial.begin(115200);
  LoRa.setPins(5, 4, 16); 

  if (!LoRa.begin(433E6)) {  
    Serial.println("LoRa init failed!");
    while (1);
  }

  Serial.println("LoRa  Initialized");

  pinMode(pot1Pin, INPUT);
  pinMode(pot2Pin, INPUT);
  pinMode(joyXPin, INPUT);
  pinMode(joyYPin, INPUT);

  // Configure joystick switch with interrupt
  pinMode(joySwitchPin, INPUT_PULLUP); // Enable pull-up resistor
  attachInterrupt(digitalPinToInterrupt(joySwitchPin), handleJoySwitch, RISING); // Interrupt on rising edge

  // Configure buzzer and LED pins as outputs
  pinMode(buzzerPin, OUTPUT);
  pinMode(redLEDPin, OUTPUT);
  pinMode(greenLEDPin, OUTPUT);
  pinMode(blueLEDPin, OUTPUT);

  // Turn off all LEDs initially
  digitalWrite(redLEDPin, LOW);
  digitalWrite(greenLEDPin, LOW);
  digitalWrite(blueLEDPin, LOW);

  analogWrite(blueLEDPin,80);
  
  startmillis = millis();
  speed_time = millis();
}

void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String incomingData = "";

    while (LoRa.available()) {
      char c = LoRa.read();
      incomingData += c; 
    }

    if (incomingData[0] == '(') {
      beacon_state = true;
      count = 80;
    }

    Serial.println(incomingData);
  }

  // Forward desktop commands (USB serial) to the rover over LoRa.
  // Non-blocking: reads only bytes already buffered from the desktop.
  if (Serial.available() > 0) {
    String cmd = "";
    while (Serial.available() > 0) {
      cmd += (char)Serial.read();
    }
    LoRa.beginPacket();
    LoRa.print(cmd);
    LoRa.endPacket();
  }



  if (millis() - startmillis > 100) {
    readSensor();
    startmillis = millis();
  }

   if (joystick != '0'){
    LoRa.beginPacket();         
    LoRa.print(joystick);        
    LoRa.endPacket();
    joystick = '0';
   }
   else if(pot1Value_change){
    LoRa.beginPacket();         
    LoRa.print("g" + String(pot1Value));       
    LoRa.endPacket();
    pot1Value_change = false;
  }
  else if (pot2Value_change) {
    LoRa.beginPacket();         
    LoRa.print("s" + String(pot2Value));        
    LoRa.endPacket();
    pot2Value_change = false;
  }
  else{
    bool currentButtonState = digitalRead(joySwitchPin);
  if (joySwitchPressed && currentButtonState == LOW && lastButtonState == HIGH) {
    LoRa.beginPacket();         
    LoRa.print('d');        
    LoRa.endPacket();
    Serial.println("ddddd");
    joySwitchPressed = false; 
  }

  lastButtonState = currentButtonState;
  }

  if(millis() - speed_time > 1000 ){
    String str = "<";
    str += String(62 - pot2Value);
    str += ",";
    str += String(24 - pot1Value);
    str += ">";
    Serial.println(str);
    speed_time = millis();
  }

  if(beacon_state && (millis() - beacon_time > 50 )){
    beacon_time = millis();
    if(count == 0){
      count = 20;
      beacon_state = false;
    }
    else if(count % 2 == 0){
      digitalWrite(buzzerPin, HIGH);
      digitalWrite(redLEDPin, HIGH);
      count -= 1;
    }
    else{
      digitalWrite(buzzerPin, LOW);
      digitalWrite(redLEDPin, LOW);
      count -= 1;
    }
  }

}
