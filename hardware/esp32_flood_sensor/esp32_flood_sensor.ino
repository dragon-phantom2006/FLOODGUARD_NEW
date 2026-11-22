// FloodGuard four-switch ESP32 firmware.
// Switch wiring: each switch connects its GPIO pin to GND when activated.
// INPUT_PULLUP is used, so LOW means ON/active.
// The switch array is ordered bottom-to-top: Tide, Yellow, Orange, Red.

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* API_URL = "http://YOUR_COMPUTER_LAN_IP:5000/api/v1/telemetry";
const char* SENSOR_ID = "YOUR_REGISTERED_SENSOR_ID";
const char* DEVICE_KEY = "YOUR_REGISTERED_DEVICE_KEY";

// ESP32 GPIO mapping (bottom-most switch first).
const uint8_t SWITCH_PINS[4] = {13, 14, 27, 26};
const uint8_t LCD_SDA_PIN = 21;
const uint8_t LCD_SCL_PIN = 22;
const uint8_t LCD_ADDRESS = 0x27; // Change to 0x3F if that is your LCD backpack address.

LiquidCrystal_I2C lcd(LCD_ADDRESS, 16, 2);
int lastDisplayedLevel = -1;
unsigned long lastPostAt = 0;
const unsigned long POST_INTERVAL_MS = 5000;

float readWaterLevelMeters() {
  // Replace this placeholder with your calibrated water-level sensor reading.
  // The four physical switches determine the displayed flood level in this sketch.
  return 0.0f;
}

int readSwitchLevel() {
  int activeLevel = 0;
  for (int index = 0; index < 4; index++) {
    if (digitalRead(SWITCH_PINS[index]) == LOW) {
      // The highest active switch wins if multiple switches are ON.
      activeLevel = index + 1;
    }
  }
  return activeLevel;
}

const char* statusLabel(int level) {
  switch (level) {
    case 1: return "Tide Alert";
    case 2: return "Yellow Level";
    case 3: return "Orange Level";
    case 4: return "Red Level";
    default: return "Normal";
  }
}

void updateLcd(int level) {
  if (level == lastDisplayedLevel) return;
  lastDisplayedLevel = level;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(statusLabel(level));
  lcd.setCursor(0, 1);

  if (level == 4) {
    lcd.print("EVACUATE NOW");
  } else if (level == 3) {
    lcd.print("Prepare to move");
  } else if (level == 2) {
    lcd.print("Stay prepared");
  } else if (level == 1) {
    lcd.print("Stay alert");
  } else {
    lcd.print("No switch active");
  }
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);

  for (int index = 0; index < 4; index++) {
    pinMode(SWITCH_PINS[index], INPUT_PULLUP);
  }

  Wire.begin(LCD_SDA_PIN, LCD_SCL_PIN);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("FloodGuard");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");

  connectWiFi();
}

void loop() {
  const int switchLevel = readSwitchLevel();
  const float waterLevel = readWaterLevelMeters();

  updateLcd(switchLevel);

  if (millis() - lastPostAt >= POST_INTERVAL_MS) {
    lastPostAt = millis();
    connectWiFi();

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(API_URL);
      http.addHeader("Content-Type", "application/json");
      http.addHeader("X-Device-Key", DEVICE_KEY);

      String body = String("{\"sensor_id\":\"") + SENSOR_ID +
        "\",\"water_level_m\":" + String(waterLevel, 3) +
        ",\"switch_level\":" + String(switchLevel) + "}";

      const int responseCode = http.POST(body);
      Serial.printf("Telemetry HTTP %d | status: %s | switch level: %d\n",
                    responseCode, statusLabel(switchLevel), switchLevel);
      http.end();
    }
  }

  delay(100);
}
