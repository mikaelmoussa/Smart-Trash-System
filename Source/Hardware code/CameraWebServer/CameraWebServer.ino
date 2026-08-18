#include "esp_camera.h"
#include <WiFi.h>

// ===========================
// Select camera model in board_config.h
// ===========================
#include "board_config.h"

// ===========================
// Enter your WiFi credentials
// ===========================
const char *ssid = "S23";
const char *password = "12345678900";

void startCameraServer();
void setupLedFlash();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 6;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();

  // OV3660 specific fixes
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }

  // ── Best settings for waste detection ────────────────
  s->set_framesize(s, FRAMESIZE_VGA);        // 640x480
  s->set_quality(s, 10);                     // sharp image
  s->set_brightness(s, 2);                   // max brightness
  s->set_contrast(s, 2);                     // max contrast
  s->set_saturation(s, -2);                  // reduce color noise
  s->set_special_effect(s, 0);               // no effect
  s->set_whitebal(s, 1);                     // auto white balance
  s->set_awb_gain(s, 1);                     // AWB gain on
  s->set_wb_mode(s, 0);                      // auto WB
  s->set_exposure_ctrl(s, 1);                // auto exposure
  s->set_aec2(s, 1);                         // AEC DSP on
  s->set_ae_level(s, 0);                     // default AE
  s->set_gain_ctrl(s, 1);                    // auto gain
  s->set_gainceiling(s, GAINCEILING_2X);     // 2x gain ceiling
  s->set_bpc(s, 1);                          // black pixel fix
  s->set_wpc(s, 1);                          // white pixel fix
  s->set_raw_gma(s, 1);                      // gamma on
  s->set_lenc(s, 1);                         // lens correction
  s->set_hmirror(s, 0);                      // no mirror
  s->set_vflip(s, 0);                        // no flip
  s->set_dcw(s, 1);                          // downsize on
  s->set_colorbar(s, 0);                     // no color bar
  // ─────────────────────────────────────────────────────

  // ── Flash LED at 100% brightness always on ───────────
  ledcAttach(4, 5000, 8);                    // GPIO 4, 5khz, 8-bit
  ledcWrite(4, 255);                         // 255/255 = 100% MAX
  // ─────────────────────────────────────────────────────

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

void loop() {
  delay(10000);
}