#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// BLE Settings
#define DEVICE_NAME          "ESP32_BT_ML_PROJECT"
#define SERVICE_UUID         "63661bda-e38c-4eb0-9389-12523579b526"
#define CHARACTERISTIC_UUID  "8fd0a2f0-e842-492b-8d9c-213e28678075"

// Audio Settings
const int SAMPLE_RATE = 22050;     // Hz
const int DURATION_SECONDS = 15;   // Max recording time
const int BUFFER_SIZE = 1024;      // Adjust based on MTU size (typically 20-512 bytes for BLE)

// BLE Objects
BLEServer *pServer;
BLEService *pService;
BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

// Audio Buffer
int16_t audioBuffer[BUFFER_SIZE];  // 16-bit signed PCM
size_t audioBufferIndex = 0;

// BLE Server Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Device connected");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Device disconnected");
    // Restart advertising to allow reconnection
    pServer->getAdvertising()->start();
  }
};

// Simulate Audio Data (Replace with actual ADC/I2S read)
void readAudioSamples() {
  for (int i = 0; i < BUFFER_SIZE; i++) {
    audioBuffer[i] = analogRead(34) - 2048;  // Simulate 12-bit ADC (0-4095) -> (-2048 to 2047)
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE Audio Streaming...");

  // Initialize BLE
  BLEDevice::init(DEVICE_NAME);
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create BLE Service
  pService = pServer->createService(SERVICE_UUID);

  // Create BLE Characteristic (Notify for streaming)
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ   |
    BLECharacteristic::PROPERTY_NOTIFY |
    BLECharacteristic::PROPERTY_WRITE_NR
  );
  pCharacteristic->addDescriptor(new BLE2902());  // Enable notifications

  // Start Service and Advertising
  pService->start();
  pServer->getAdvertising()->start();
  Serial.println("BLE Ready. Waiting for client...");
}

void loop() {
  if (deviceConnected) {
    // 1. Read audio samples (replace with actual ADC/I2S code)
    readAudioSamples();

    // 2. Send via BLE (chunked to avoid MTU limits)
    pCharacteristic->setValue((uint8_t*)audioBuffer, BUFFER_SIZE * sizeof(int16_t));
    pCharacteristic->notify();
    delay(10);  // Adjust based on sample rate and buffer size
  }
}