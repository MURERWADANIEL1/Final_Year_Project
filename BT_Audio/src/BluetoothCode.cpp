#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include "esp_bt_device.h"
#include "esp_gap_ble_api.h"

// UUIDs
#define SERVICE_UUID        "63661bda-e38c-4eb0-9389-12523579b526"
#define CHARACTERISTIC_UUID "8fd0a2f0-e842-492b-8d9c-213e28678075"

BLEServer* pServer = nullptr;
BLECharacteristic* pCharacteristic = nullptr;

bool deviceConnected = false;
bool oldDeviceConnected = false;
unsigned long lastNotifyTime = 0;
const unsigned long notifyInterval = 1000; // 1 second

// Server Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    deviceConnected = true;
    Serial.println("Device connected");
  }

  void onDisconnect(BLEServer* pServer) override {
    deviceConnected = false;
    Serial.println("Device disconnected");
  }
};

// Security Callbacks
class MySecurity : public BLESecurityCallbacks {
  uint32_t onPassKeyRequest() {
    Serial.println("Passkey Requested");
    return 123456;
  }

  void onPassKeyNotify(uint32_t pass_key) {
    Serial.print("Passkey for pairing: ");
    Serial.println(pass_key);
  }

  bool onConfirmPIN(uint32_t pass_key) {
    Serial.print("Confirm Passkey: ");
    Serial.println(pass_key);
    return true;
  }

  bool onSecurityRequest() {
    Serial.println("Security Requested");
    return true;
  }

  void onAuthenticationComplete(esp_ble_auth_cmpl_t cmpl) {
    if (cmpl.success) {
      Serial.println("Authentication success");
    } else {
      Serial.println("Authentication failed");
    }
  }
};

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Starting BLE...");
  BLEDevice::init("ESP32_Audio_Test");
  Serial.println(BLEDevice::getAddress().toString().c_str());


  // Create BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create BLE Service
  BLEService* pService = pServer->createService(SERVICE_UUID);

  // Create BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_WRITE |
    BLECharacteristic::PROPERTY_NOTIFY |
    BLECharacteristic::PROPERTY_INDICATE
  );

  pCharacteristic->setValue("Hello from ESP32");
  pCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Advertise BLE
  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x06);  // Recommended for Android
  BLEDevice::startAdvertising();

  Serial.println("BLE advertising started");

  // Set up BLE security
  BLESecurity *pSecurity = new BLESecurity();
  pSecurity->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_MITM_BOND);
  pSecurity->setCapability(ESP_IO_CAP_OUT);  // Device shows passkey
  pSecurity->setInitEncryptionKey(ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK);
  pSecurity->setRespEncryptionKey(ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK);
  pSecurity->setKeySize(16);
  pSecurity->setStaticPIN(123456);  // Use this instead of setStaticPasskey
  BLEDevice::setSecurityCallbacks(new MySecurity());
}

void loop() {
  unsigned long currentMillis = millis();

  if (deviceConnected && (currentMillis - lastNotifyTime >= notifyInterval)) {
    if (pCharacteristic != nullptr) {
      pCharacteristic->setValue("New value from ESP32");
      pCharacteristic->notify();
      Serial.println("Notified client");
    }
    lastNotifyTime = currentMillis;
  }

  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    BLEDevice::startAdvertising();
    Serial.println("Restarted advertising");
    oldDeviceConnected = deviceConnected;
  }

  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }
}
