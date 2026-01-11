#include <Wire.h>
#include <Adafruit_BME280.h>

// I2C 1 (Default) -> SDA: 8, SCL: 9
// I2C 2 (Secondary) -> SDA: 17, SCL: 18
// Note: You can change these #define values to match your wiring
#define SDA1_PIN 8
#define SCL1_PIN 9

#define SDA2_PIN 17
#define SCL2_PIN 18

// I2C address of BME280 (Both can be 0x76 now because they are on different buses)
#define BME1_ADDR 0x76
#define BME2_ADDR 0x76 

Adafruit_BME280 bme1;
Adafruit_BME280 bme2;

// Create a second I2C bus instance
TwoWire I2Ctwo = TwoWire(1);

// Analog pins for Soil Sensors
// ESP32-S3 ADC pins: GPIO 1-10 are ADC1, GPIO 11-20 are ADC2.
// WARNING: GPIO 4 and 5 are also defined as RELAY1/REVLAY2 below. 
// Soil Sensors MUST use different pins if Relays use 4/5. 
// I will set them to 12 and 13 to avoid conflict.
#define SOIL_SENSOR_1 12
#define SOIL_SENSOR_2 13

// Relays
#define RELAY1 4
#define RELAY2 5
#define RELAY3 6
#define RELAY4 7
#define RELAY5 15 // Changed from 1 (UART TX)
#define RELAY6 16 // Changed from 2 (UART RX)
#define RELAY7 42 // Valid on S3
#define RELAY8 41 // Valid on S3

bool bme1_ok = false;
bool bme2_ok = false;

void setup() {
  Serial.begin(115200);
  
  // Wait for Serial to be ready (useful for Native USB) - but don't hang if no PC connected
  // delay(2000); 

  Serial.setTimeout(50); 
  
  // Init I2C buses
  Wire.begin(SDA1_PIN, SCL1_PIN);     // Bus 0
  I2Ctwo.begin(SDA2_PIN, SCL2_PIN);   // Bus 1

  // Init BME sensors on separate buses
  // bme1 uses default 'Wire' (Bus 0)
  bme1_ok = bme1.begin(BME1_ADDR, &Wire);
  if (!bme1_ok) bme1_ok = bme1.begin(0x77, &Wire); // Try 0x77 if 0x76 fails

  // bme2 uses 'I2Ctwo' (Bus 1)
  bme2_ok = bme2.begin(BME2_ADDR, &I2Ctwo); 
  if (!bme2_ok) bme2_ok = bme2.begin(0x77, &I2Ctwo); // Try 0x77 if 0x76 fails

  if (!bme1_ok) Serial.println("WARNING: BME1 not found on Bus 1 (SDA:8, SCL:9)");
  if (!bme2_ok) Serial.println("WARNING: BME2 not found on Bus 2 (SDA:17, SCL:18)");

  // Setup Relays
  int relays[] = {RELAY1, RELAY2, RELAY3, RELAY4, RELAY5, RELAY6, RELAY7, RELAY8};
  for (int pin : relays) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);  // Active LOW or HIGH? Previous code set HIGH (OFF likely for active-low modules)
  }
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "get_temp_all") {
      float t1 = 0, h1 = 0, t2 = 0, h2 = 0;
      
      if (bme1_ok) {
        t1 = bme1.readTemperature();
        h1 = bme1.readHumidity();
        // Format strictly matching what Python expects: "BME1 TEMP: %.2f C, HUMID: %.2f %%"
        Serial.printf("BME1 TEMP: %.2f C, HUMID: %.2f %%\n", t1, h1);
      } else {
        Serial.println("BME1 ERROR"); // Python will ignore this line as it doesn't match pattern
      }
      
      delay(10); // Small delay to prevent easy buffer merging if python reads fast

      if (bme2_ok) {
        t2 = bme2.readTemperature();
        h2 = bme2.readHumidity();
        Serial.printf("BME2 TEMP: %.2f C, HUMID: %.2f %%\n", t2, h2);
      } else {
        Serial.println("BME2 ERROR");
      }
    }

    else if (cmd == "get_soil") {
      int soil1 = analogRead(SOIL_SENSOR_1);
      int soil2 = analogRead(SOIL_SENSOR_2);
      
      // Standardize ADC width if needed? ESP32 is 12-bit (0-4095).
      Serial.printf("SOIL1: %d\n", soil1);
      delay(10);
      Serial.printf("SOIL2: %d\n", soil2);
    }

    else if (cmd.startsWith("relay_on")) {
      int num = cmd.substring(9).toInt();
      controlRelay(num, LOW); // Assume Active LOW (ON=LOW) based on setup
      Serial.printf("RELAY %d ON\n", num);
    }

    else if (cmd.startsWith("relay_off")) {
      int num = cmd.substring(10).toInt();
      controlRelay(num, HIGH);
      Serial.printf("RELAY %d OFF\n", num);
    }
    
    // Catch-all for clearing buffer or debugging
    else if (cmd.length() > 0) {
      Serial.printf("UNKNOWN: %s\n", cmd.c_str());
    }
  }
}

void controlRelay(int num, int state) {
  int pin = -1;
  switch (num) {
    case 1: pin = RELAY1; break;
    case 2: pin = RELAY2; break;
    case 3: pin = RELAY3; break;
    case 4: pin = RELAY4; break;
    case 5: pin = RELAY5; break;
    case 6: pin = RELAY6; break;
    case 7: pin = RELAY7; break;
    case 8: pin = RELAY8; break;
  }
  
  if (pin != -1) {
    digitalWrite(pin, state);
  }
}
