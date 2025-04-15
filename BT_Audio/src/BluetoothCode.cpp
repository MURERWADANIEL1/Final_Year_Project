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

const int Mic=34;
#define BUFFER_SIZE 256
uint8_t audioBuffer[BUFFER_SIZE];

unsigned long lastNotifyTime = 0;
const unsigned long notifyInterval = 20; 

unsigned long startTime=0;
bool started =false;

// Server Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    deviceConnected = true;
    Serial.println("Device connected");
  }

  void onDisconnect(BLEServer* pServer) override {
    deviceConnected = false;
    Serial.println("Device disconnected");
    delay(100);
    pServer->getAdvertising()->start();
    Serial.println("Restarted Advertising");
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
  BLEDevice::init("ESP32_BT_ML_PROJECT");
  
  Serial.println(BLEDevice::getAddress().toString().c_str());

  // Create BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create BLE Service
  BLEService* pService = pServer->createService(SERVICE_UUID);

  // Create BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_NOTIFY 
  );

  pCharacteristic->setValue("Hello from ESP32");
  pCharacteristic->addDescriptor(new BLE2902());
  pService->start();
  pServer->getAdvertising()->start();

    // Advertise BLE
  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x06);  // Recommended for Android
  BLEDevice::startAdvertising();

  analogReadResolution(12);
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

  if (deviceConnected) {
    // Notify client every second
    if (!started){
      startTime=millis();
      started=true;
      Serial.println("Start Streaming Audio");      
    }

    if (millis() - startTime <= 15000) {
      for (int i = 0; i < BUFFER_SIZE; i++) {
        int val = analogRead(Mic);   // 0–4095
        audioBuffer[i] = val >> 4;   // Scale to 8-bit
      }
      //Send Data
      pCharacteristic->setValue(audioBuffer, BUFFER_SIZE);
      pCharacteristic->notify();
      delay(20);
    }

  } else{
    started=false;
  }

}
