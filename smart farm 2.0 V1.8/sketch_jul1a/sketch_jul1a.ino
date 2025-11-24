#include <Wire.h>
#include <Adafruit_BME280.h>

// I2C address ของ BME280
#define BME1_ADDR 0x76
#define BME2_ADDR 0x77

Adafruit_BME280 bme1;
Adafruit_BME280 bme2;

// ขา Analog สำหรับ Soil Sensor
#define SOIL_SENSOR_1 34
#define SOIL_SENSOR_2 35

// รีเลย์ 4 ตัว
#define RELAY1 5
#define RELAY2 6
#define RELAY3 7
#define RELAY4 8

bool bme1_ok = false;
bool bme2_ok = false;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  bme1_ok = bme1.begin(BME1_ADDR);
  bme2_ok = bme2.begin(BME2_ADDR);

  if (!bme1_ok) Serial.println("ERROR: ไม่พบ BME280 ตัวที่ 1");
  if (!bme2_ok) Serial.println("ERROR: ไม่พบ BME280 ตัวที่ 2");

  // กำหนดขารีเลย์
  for (int pin : {RELAY1, RELAY2, RELAY3, RELAY4}) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);  // ปิดทั้งหมด
  }
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "get_temp_all") {
      if (bme1_ok) {
        float t1 = bme1.readTemperature();
        float h1 = bme1.readHumidity();
        Serial.printf("BME1 TEMP: %.2f C, HUMID: %.2f %%\n", t1, h1);
        delay(10);
      } else {
        Serial.println("BME1 NOT RESPONDING");
        delay(10);
      }

      if (bme2_ok) {
        float t2 = bme2.readTemperature();
        float h2 = bme2.readHumidity();
        Serial.printf("BME2 TEMP: %.2f C, HUMID: %.2f %%\n", t2, h2);
        delay(10);
      } else {
        Serial.println("BME2 NOT RESPONDING");
        delay(10);
      }
    }

    else if (cmd == "get_soil") {
      int soil1 = analogRead(SOIL_SENSOR_1);
      int soil2 = analogRead(SOIL_SENSOR_2);
      Serial.printf("SOIL1: %d\n", soil1);
      delay(10);
      Serial.printf("SOIL2: %d\n", soil2);
      delay(10);
    }

    else if (cmd.startsWith("relay_on")) {
      int num = cmd.substring(9).toInt();
      setRelay(num, LOW);
      Serial.printf("RELAY %d ON\n", num);
      delay(10);
    }

    else if (cmd.startsWith("relay_off")) {
      int num = cmd.substring(10).toInt();
      setRelay(num, HIGH);
      Serial.printf("RELAY %d OFF\n", num);
      delay(10);
    }

    else {
      Serial.println("UNKNOWN CMD");
      delay(10);
    }
  }
}

void setRelay(int num, int state) {
  switch (num) {
    case 1: digitalWrite(RELAY1, state); break;
    case 2: digitalWrite(RELAY2, state); break;
    case 3: digitalWrite(RELAY3, state); break;
    case 4: digitalWrite(RELAY4, state); break;
    default:
      Serial.printf("INVALID RELAY NUMBER: %d\n", num);
      delay(10);
  }
}
