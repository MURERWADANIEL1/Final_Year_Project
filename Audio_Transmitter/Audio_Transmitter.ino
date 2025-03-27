/*
Applying Multiprocessing Capability of ESP32 to transfer audio files over Bluetooth

1. First define RTOS for time-critical operations
2. Set ADC operation on core 1 and Queue operation for next stage 
3. Perform DSP on signal before transmission on core 2 and Queue it
4. Set the channel for transmitting data to a Remote Place using Bluetooth Classic
*/
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <Arduino.h>
#include "BluetoothSerial.h"

#define ADC_PIN 34  // Change if needed
#define SAMPLE_RATE 22050
#define BUFFER_SIZE 256  // Adjust based on performance testing
#define FILTER_TAP_NUM 21  // Number of FIR filter taps

BluetoothSerial SerialBT;
TaskHandle_t Task1, Task2;
int16_t adcBuffer[BUFFER_SIZE];
volatile bool bufferReady = false;
float dcOffset = 0;
/*
// FIR Low-pass filter coefficients (generated for 2000Hz cutoff at 22050Hz sampling rate)
const float firCoeffs[FILTER_TAP_NUM] = {
    -0.001822, -0.005123, -0.008299, -0.007504,  0.002867,
     0.022202,  0.044743,  0.059408,  0.054436,  0.022835,
    -0.028877, -0.080159, -0.107253, -0.092532, -0.035822,
     0.046137,  0.120267,  0.152256,  0.120267,  0.046137,
    -0.035822
};

float firBuffer[FILTER_TAP_NUM] = {0};

// Function to apply FIR filter
int16_t applyFIRFilter(int16_t newSample) {
    memmove(&firBuffer[1], &firBuffer[0], (FILTER_TAP_NUM - 1) * sizeof(float));
    firBuffer[0] = newSample - dcOffset;  // Remove DC bias
    float filteredSample = 0;
    for (int i = 0; i < FILTER_TAP_NUM; i++) {
        filteredSample += firBuffer[i] * firCoeffs[i];
    }
    return (int16_t)filteredSample;
}

*/
/*
// ADC Sampling Task (Core 1)
void IRAM_ATTR adcSamplingTask(void *parameter) {
    while (1) {
        float sum = 0;
        for (int i = 0; i < BUFFER_SIZE; i++) {
            int16_t rawSample = analogRead(ADC_PIN);  // Read ADC
            sum += rawSample;
            adcBuffer[i] = applyFIRFilter(rawSample); // Apply FIR filter
        }
        dcOffset = sum / BUFFER_SIZE;  // Update DC bias
        bufferReady = true;
        vTaskDelay(pdMS_TO_TICKS(1000 * BUFFER_SIZE / SAMPLE_RATE));
    }
}
*/
// Bluetooth Transmission Task (Core 2)
void bluetoothTask(void *parameter) {
    while (1) {
        if (bufferReady) {
            SerialBT.write((uint8_t *)adcBuffer, BUFFER_SIZE * sizeof(int16_t));
            bufferReady = false;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void setup() {
    Serial.begin(115200);
    SerialBT.begin("ESP32-Audio");
    pinMode(ADC_PIN, INPUT);
    
   // xTaskCreatePinnedToCore(adcSamplingTask, "ADC Sampling", 4096, NULL, 1, &Task1, 0);
   // xTaskCreatePinnedToCore(bluetoothTask, "Bluetooth Tx", 4096, NULL, 1, &Task2, 1);
}

void loop() {
    // Nothing here, tasks handle everything
}
