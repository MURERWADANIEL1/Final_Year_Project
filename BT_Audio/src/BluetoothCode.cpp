#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// BLE Settings
#define DEVICE_NAME "ESP32_BT_ML_PROJECT"
#define SERVICE_UUID "63661bda-e38c-4eb0-9389-12523579b526"
#define CHARACTERISTIC_UUID "8fd0a2f0-e842-492b-8d9c-213e28678075"

// Audio Settings
const int SAMPLE_RATE = 22050;
const int BUFFER_SIZE = 128;  // Reduced to 128 samples (256 bytes)
const int CHUNK_SIZE = 20;    // BLE packets per notification

// BLE Objects
BLEServer *pServer;
BLEService *pService;
BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("✅ Client connected!");
    BLEDevice::setMTU(517);  // Max supported by ESP32
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("⚠️ Client disconnected!");
  }
};

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE...");
  
  BLEDevice::init(DEVICE_NAME);
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  pService = pServer->createService(SERVICE_UUID);
  
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_NOTIFY |
    BLECharacteristic::PROPERTY_WRITE_NR
  );
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->start();
  Serial.println("BLE Ready!");
}

void loop() {
  if (deviceConnected) {
    int16_t audioBuffer[BUFFER_SIZE];
    
    // Simulate audio (replace with actual ADC/I2S read)
    for(int i=0; i<BUFFER_SIZE; i++) {
      audioBuffer[i] = random(-32768, 32767); 
    }

    // Send in chunks (20 bytes per packet)
    for(int i=0; i<BUFFER_SIZE; i+=CHUNK_SIZE) {
      int chunk_len = min(CHUNK_SIZE, BUFFER_SIZE-i);
      pCharacteristic->setValue((uint8_t*)&audioBuffer[i], chunk_len*2);
      pCharacteristic->notify();
      delay(10);  // ~22050 samples/sec rate
    }
    
    Serial.printf("Sent %d samples\n", BUFFER_SIZE);
  }
  delay(1000);
}