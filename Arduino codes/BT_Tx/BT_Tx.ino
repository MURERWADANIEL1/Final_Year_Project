
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// BLE Service and Characteristic UUIDs (Change these!)
#define SERVICE_UUID "63661bda-e38c-4eb0-9389-12523579b526" // Replace with your service UUID
#define CHARACTERISTIC_UUID "8fd0a2f0-e842-492b-8d9c-213e28678075" // Replace with your characteristic UUID

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
    }
};

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE work!");

  // Create the BLE Device
  BLEDevice::init("ESP32-BLE-Test"); // Give it a name

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // functions that help with iPhone connections
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("Waiting a client connection to notify...");
}

void loop() {
  // Disconnect
  if (!deviceConnected && oldDeviceConnected) {
      delay(500); // give the bluetooth stack the chance to get things ready
      pServer->startAdvertising(); // restart advertising
      Serial.println("Start advertising");
      oldDeviceConnected = deviceConnected;
  }
  // Connect
  if (deviceConnected && !oldDeviceConnected) {
      // do stuff here on connecting
      oldDeviceConnected = deviceConnected;
  }
  // Check if data is available from the BLE connection
  if (deviceConnected && pCharacteristic->getValue().length() > 0) {
    std::string rxValue = pCharacteristic->getValue();
    Serial.print("Received Value: ");
    Serial.println(rxValue.c_str());
    pCharacteristic->setValue(rxValue);
    pCharacteristic->notify();
  }
  delay(100);
}
