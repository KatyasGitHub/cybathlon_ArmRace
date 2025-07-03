#include <esp32cam.h>
#include <WebServer.h>
#include <WiFi.h>
#include "esp_camera.h"         
#include "img_converters.h"

// #define AP_SSID "CybathlonCamera"
// #define AP_PASS "BestTeam2025"

// ======【★ Change this to your own WiFi name and password★】======
#define WIFI_SSID "PYUR D9B7F"
#define WIFI_PASS "4U4uBs77bQnn"
// ===========================================

#define FLASH_PIN 4               

WebServer server(80);

void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) { server.send(500,"text/plain","capture failed"); return; }

  uint8_t* jpgBuf; size_t jpgLen;
  frame2jpg(fb, 80, &jpgBuf, &jpgLen);
  esp_camera_fb_return(fb);

  server.setContentLength(jpgLen);
  server.send(200, "image/jpeg");
  server.client().write(jpgBuf, jpgLen);
  free(jpgBuf);
}

/* ───────────── MJPEG stream endpoint ─────────────
   Content-Type: multipart/x-mixed-replace; boundary=frame
   Each part is a full JPEG; browsers / OpenCV treat it as video                */
void handleStream() {
  WiFiClient  client = server.client();
  const char* BOUND = "frame";

  client.print(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary="
    + String(BOUND) + "\r\n\r\n");

  while (client.connected()) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) continue;

    uint8_t* jpgBuf; size_t jpgLen;
    bool ok = frame2jpg(fb, 80, &jpgBuf, &jpgLen);
    esp_camera_fb_return(fb);
    if (!ok) continue;

    client.printf("--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
                  BOUND, (unsigned)jpgLen);
    client.write(jpgBuf, jpgLen);
    client.print("\r\n");
    free(jpgBuf);

    delay(40);                         // ≈25 fps; raise to 100 for ~10 fps
  }
}

/* ───────────── HTML preview (optional) ───────────── */
void handleRoot() {
  server.send(200, "text/html",
    "<!DOCTYPE html><title>ESP32-CAM</title>"
    "<style>body{margin:0}</style>"
    "<img src='/stream' style='width:100%'>");
}

/* ---------- setup() ---------- */
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(FLASH_PIN, OUTPUT);      // <─ NEW: allow direct LED control
  digitalWrite(FLASH_PIN, LOW);    // start with LED off

    // ======【★ 这里改为开机自动点亮闪光灯 ★】======
  // digitalWrite(FLASH_PIN, HIGH);    // 开机自动点亮闪光灯

  auto res = esp32cam::Resolution::find(640, 480);
  esp32cam::Config cfg;
  cfg.setPins(esp32cam::pins::AiThinker);
  cfg.setResolution(res);              // VGA
  if (!esp32cam::Camera.begin(cfg)) {
    Serial.println("Camera init failed"); while (true) {}
  }

  // // Wi-Fi soft-AP
  // WiFi.softAP(AP_SSID, AP_PASS);
  // Serial.print("AP IP: "); Serial.println(WiFi.softAPIP());


 // ======【★ STA mode: let ESP32 connect to your home WiFi router ★】======
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connection successful! ESP32's LAN IP is:");
  Serial.println(WiFi.localIP());
  // ===============================================


  // routes
  server.on("/",           HTTP_GET, handleRoot);
  server.on("/capture.jpg",HTTP_GET, handleCapture);
  server.on("/stream",     HTTP_GET, handleStream);
  server.begin();
}

/* ---------- loop() ---------- */
void loop() {
  server.handleClient();

  /* --- NEW: simple serial command parser --- */
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'F' || cmd == 'f') {
      digitalWrite(FLASH_PIN, HIGH);      // torch ON
      Serial.println("Flash ON");
    }
    else if (cmd == 'O' || cmd == 'o') {
      digitalWrite(FLASH_PIN, LOW);       // torch OFF
      Serial.println("Flash OFF");
    }
  }
}
