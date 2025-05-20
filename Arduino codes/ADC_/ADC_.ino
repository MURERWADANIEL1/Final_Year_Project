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
#define PASSKEY 123456  

// Audio Settings
const int CHUNK_SIZE = 20;
const float SAMPLE_RATE = 22050.0;
uint32_t currentSampleIndex = 0;

BLEServer *pServer;
BLEService *pService;
BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

void setupMic() {
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);
}

// BLE Server Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) override {
        deviceConnected = true;
        Serial.println("Client connected!");
        BLEDevice::setPower(ESP_PWR_LVL_P9);
    }
    void onDisconnect(BLEServer* pServer) override {
        deviceConnected = false;
        Serial.println("Client disconnected!");
        BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
        pAdvertising->start();
        Serial.println("Advertising restarted");
    }
};

// BLE Security Callbacks
class MySecurityCallbacks : public BLESecurityCallbacks {
    uint32_t onPassKeyRequest() override {
        Serial.println("PassKey Request");
        return PASSKEY;
    }

    void onPassKeyNotify(uint32_t pass_key) override {
        Serial.print("PassKey: "); 
        Serial.println(pass_key);
    }

    bool onSecurityRequest() override {
        Serial.println("Security Request");
        return true;
    }

    void onAuthenticationComplete(esp_ble_auth_cmpl_t cmpl) override {
        Serial.println(cmpl.success ? "Pairing Success!" : "Pairing Failed");
    }

    bool onConfirmPIN(uint32_t pin) override {
        Serial.print("Confirm PIN: "); 
        Serial.println(pin);
        return true;
    }
};

void setup() {
    Serial.begin(115200);
    Serial.println("Starting BLE...");

    BLEDevice::init(DEVICE_NAME);

    BLESecurity *pSecurity = new BLESecurity();
    pSecurity->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_BOND);
    pSecurity->setCapability(ESP_IO_CAP_NONE);
    pSecurity->setKeySize(16);
    BLEDevice::setSecurityCallbacks(new MySecurityCallbacks());

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
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::setPower(ESP_PWR_LVL_P9);
    pAdvertising->start();

    Serial.println("BLE Ready! Waiting for connections...");
    setupMic();
}

// Simulate noisy chirp-like audio (non-sine, frequency-varying square-like)
int16_t readMicSample() {
    float t = (float)currentSampleIndex / SAMPLE_RATE;

    // Vary the frequency nonlinearly over time (pseudo-chirp)
    float freq = 200.0 + 1000.0 * fabs(sin(2 * PI * 0.25 * t));  // Sweep 200–1200 Hz

    // Create a square wave with changing frequency and slight noise
    float cycle = fmod(t * freq, 1.0);
    float square = (cycle < 0.5) ? 1.0 : -1.0;

    // Add harmonic component and noise
    float noise = (float)(random(-1000, 1000)) / 32768.0f;
    float sample = square + 0.3f * sin(2 * PI * freq * 3 * t) + 0.2f * noise;

    sample = constrain(sample, -1.0f, 1.0f);  // Safety
    int16_t value = (int16_t)(sample * 32767);
    currentSampleIndex++;
    return value;
}

void loop() {
    if (deviceConnected) {
        uint8_t buffer[CHUNK_SIZE * 2];

        for (int i = 0; i < CHUNK_SIZE; i++) {
            int16_t sample = readMicSample();
            buffer[i * 2] = sample & 0xFF;
            buffer[i * 2 + 1] = (sample >> 8) & 0xFF;
        }

        pCharacteristic->setValue(buffer, CHUNK_SIZE * 2);
        pCharacteristic->notify();

        delay(20);
    }
}
