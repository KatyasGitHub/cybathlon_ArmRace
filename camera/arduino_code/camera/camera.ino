#include <esp32cam.h>
#include <WebServer.h>
#include <WiFi.h>
#include "esp_camera.h"          // pull in frame2jpg()
#include "img_converters.h"

#define AP_SSID "CybathlonCamera"
#define AP_PASS "BestTeam2025"

const uint32_t PERIOD_MS = 200;      // 5 fps example
uint32_t last = 0;

WebServer server(80);

/*
void handleCapture() {
  auto img = esp32cam::capture();
  if (img == nullptr) {
    Serial.println("Capture failed");
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }
  server.setContentLength(img->size());
  server.send(200, "image/bmp");
  WiFiClient client = server.client();
  img->writeTo(client);
  Serial.println("Capture success");
}
*/

void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();  // grab RGB frame
  if (!fb) { server.send(500,"text/plain","capture failed"); return; }

  uint8_t* jpgBuf; size_t jpgLen;
  frame2jpg(fb, 80, &jpgBuf, &jpgLen);    // SW-encode to JPEG
  esp_camera_fb_return(fb);               // release buffer

  server.setContentLength(jpgLen);
  server.send(200, "image/jpeg");
  server.client().write(jpgBuf, jpgLen);  // send to browser
  free(jpgBuf);                           // tidy up
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Booting...");

  auto res = esp32cam::Resolution::find(640, 480);  // safer resolution
  esp32cam::Config cfg;
  cfg.setPins(esp32cam::pins::AiThinker);
  cfg.setResolution(res);
  //cfg.setRgb();  

  if (!esp32cam::Camera.begin(cfg)) {
    Serial.println("Camera init failed!");
    while (true) {}
  }

  Serial.println("Camera init success");

  WiFi.softAP(AP_SSID, AP_PASS);
  server.on("/capture.jpg", handleCapture);
  server.on("/", HTTP_GET, []() {                           // <-- new
    server.send(200, "text/html",
        "<!DOCTYPE html><meta http-equiv='refresh' content='1'>"
        "<img src=\"/capture.jpg\" style=\"width:100%;height:auto\">");
  }); 
  server.begin();
}

void loop() {
  server.handleClient();
}