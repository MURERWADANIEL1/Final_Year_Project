#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <BluetoothSerial.h>


#define SERVICE_UUID        "63661bda-e38c-4eb0-9389-12523579b526"
#define CHARACTERISTIC_UUID "8fd0a2f0-e842-492b-8d9c-213e28678075"

BLEServer *pServer =NULL;
BLECharacteristic *pCharacteristic = NULL;

bool deviceConnected=false;
bool oldDeviceConnected=false;

class MyServerCallbacks: public BLEServerCallbacks{
  void onConnect(BLEServer* pServer){
    deviceConnected=true;
    
  };

  void onDisconnect(BLEServer* pServer){
    deviceConnected=false;

  };
};


void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE Work");
  Serial.print("Bluetooth Device MAC Address: ");
  serial.println(BLEDevice::getAddress().toString().c_str());
  BLEDevice::init("ESP32_Audio_Test");

  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);
  BLECharacteristic *pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_WRITE |
    BLECharacteristic::PROPERTY_NOTIFY |
    BLECharacteristic::PROPERTY_INDICATE
  );
  pCharacteristic->setValue("Hello from ESP32");
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);
  BLEDevice::startAdvertising();
  Serial.println("BLE Advertising Started");
}

void loop() {
  // Add logic here for interaction if needed
}
