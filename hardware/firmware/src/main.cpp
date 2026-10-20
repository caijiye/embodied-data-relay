#include <WiFi.h>
#include <HTTPClient.h>

#include "secrets.h"

constexpr int PIN_FAN_PWM = 5;
constexpr int PIN_FAN_TACH = 4;
constexpr int PIN_NTC = 1;

volatile uint32_t tach_pulses = 0;
unsigned long last_tach_ms = 0;
unsigned long last_post_ms = 0;

void IRAM_ATTR tachISR() {
  tach_pulses++;
}

float readNtcC() {
  int mv = analogReadMilliVolts(PIN_NTC);
  if (mv <= 0) {
    return NAN;
  }
  const float series_ohm = 10000.0f;
  const float supply_mv = 3300.0f;
  float r_ntc = series_ohm * (supply_mv - (float)mv) / (float)mv;
  const float beta = 3950.0f;
  const float t0_k = 298.15f;
  const float r0_ohm = 10000.0f;
  float inv_t = 1.0f / t0_k + log(r_ntc / r0_ohm) / beta;
  return 1.0f / inv_t - 273.15f;
}

float readFanRpm() {
  uint32_t pulses;
  noInterrupts();
  pulses = tach_pulses;
  tach_pulses = 0;
  interrupts();

  unsigned long now = millis();
  float dt = (now - last_tach_ms) / 1000.0f;
  last_tach_ms = now;
  if (dt <= 0.0f) {
    return 0.0f;
  }
  return (pulses / 2.0f) * (60.0f / dt);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_FAN_TACH, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_FAN_TACH), tachISR, FALLING);
  pinMode(PIN_FAN_PWM, OUTPUT);
  analogWrite(PIN_FAN_PWM, 160);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("WiFi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  float temp = readNtcC();
  int duty = 160;
  if (!isnan(temp)) {
    duty = (int)constrain(map((long)temp, 35, 70, 80, 255), 0, 255);
  }
  analogWrite(PIN_FAN_PWM, duty);

  if (WiFi.status() == WL_CONNECTED && millis() - last_post_ms >= 5000) {
    last_post_ms = millis();
    float rpm = readFanRpm();
    char body[256];
    snprintf(body, sizeof(body),
             "{\"temperature_c\":%.1f,\"fan_rpm\":%.0f,\"fan_duty\":%d,\"rssi\":%d,\"uptime_s\":%lu}",
             isnan(temp) ? -1.0f : temp, rpm, duty, WiFi.RSSI(), millis() / 1000UL);
    HTTPClient http;
    http.begin(String(SERVER_URL) + "/api/telemetry");
    http.addHeader("Content-Type", "application/json");
    int code = http.POST((uint8_t *)body, strlen(body));
    Serial.printf("POST %d %s\n", code, body);
    http.end();
  }
  delay(200);
}
