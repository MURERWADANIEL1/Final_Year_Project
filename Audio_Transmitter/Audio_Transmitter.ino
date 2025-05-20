#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define MIC_PIN 34  // ADC1_CHANNEL_6

// BLE Settings
#define DEVICE_NAME "ESP32_ML_PROJECT"
#define SERVICE_UUID "63661bda-e38c-4eb0-9389-12523579b526"
#define CHARACTERISTIC_UUID "8fd0a2f0-e842-492b-8d9c-213e28678075"
#define PASSKEY 123456  // Change this for production

// Audio Settings
const int BUFFER_SIZE = 128;
const int CHUNK_SIZE = 20;

BLEServer *pServer;
BLEService *pService;
BLECharacteristic *pCharacteristic;
bool deviceConnected = false;
uint16_t conn_id;

void setupMic() {
    analogReadResolution(12);  // ESP32 default is 12-bit: 0–4095
    analogSetAttenuation(ADC_11db);  // allows input voltage up to ~3.6V
}

// Server Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Client connected!");
        BLEDevice::setPower(ESP_PWR_LVL_P9);
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("Client disconnected!");
        // Restart advertising
        BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
        pAdvertising->start();
        Serial.println("Advertising restarted");
    }
};

// Security Callbacks Implementation
class MySecurityCallbacks : public BLESecurityCallbacks {
    uint32_t onPassKeyRequest() {
        Serial.println("PassKey Request");
        return PASSKEY;
    }

    void onPassKeyNotify(uint32_t pass_key) {
        Serial.print("PassKey: "); Serial.println(pass_key);
    }

    bool onSecurityRequest() {
        Serial.println("Security Request");
        return true;
    }

    void onAuthenticationComplete(esp_ble_auth_cmpl_t cmpl) {
        Serial.println(cmpl.success ? "Pairing Success!" : "Pairing Failed");
    }

    bool onConfirmPIN(uint32_t pin) {
        Serial.print("Confirm PIN: "); Serial.println(pin);
        return true;
    }
};

void setup() {
    Serial.begin(115200);
    Serial.println("Starting BLE...");

    // Initialize BLE
    BLEDevice::init(DEVICE_NAME);

     // Set MTU to 517 bytes (or the maximum supported by ESP32)
    //BLEDevice::setMTU(247);  // Add this line to set a larger MTU size
    
    // Setup Security
    BLESecurity *pSecurity = new BLESecurity();
    pSecurity->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_BOND);
    pSecurity->setCapability(ESP_IO_CAP_NONE);
    pSecurity->setKeySize(16);
    BLEDevice::setSecurityCallbacks(new MySecurityCallbacks());

    // Create Server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create Service
    pService = pServer->createService(SERVICE_UUID);
    
    // Create Characteristic
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_NOTIFY |
        BLECharacteristic::PROPERTY_WRITE_NR
    );
    
    // Add Descriptor
    pCharacteristic->addDescriptor(new BLE2902());
    
    // Start Service
    pService->start();

    // Setup Advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::setPower(ESP_PWR_LVL_P9);
    pAdvertising->start();
    
    Serial.println("BLE Ready! Waiting for connections...");

    setupMic();

}

int16_t readMicSample() {
    int raw = analogRead(MIC_PIN);  // Read 0–4095
    int16_t centered = (int16_t)(raw - 2048);  // Center to roughly -2048 to +2047
    return centered << 4;  // Convert to full 16-bit dynamic range
}

void loop() {
    if (deviceConnected) {
        const int chunkSize = 200; // 200 samples
        uint8_t buffer[chunkSize * 2]; // 16-bit samples, so *2 bytes

        for (int i = 0; i < chunkSize; i++) {
            int16_t sample = readMicSample();
            buffer[i*2] = sample & 0xFF;
            buffer[i*2+1] = (sample >> 8) & 0xFF;
        }

        pCharacteristic->setValue(buffer, chunkSize * 2);
        pCharacteristic->notify();
    }
}
