/*
Applying Multiprocessing Capability of ESP32 to transfer audio files over Bluetooth

1. First define RTOS for time-critical operations
2. Set ADC operation on core 1 and Queue operation for next stage 
3. Perform DSP on signal before transmission on core 2 and Queue it
4. Set the channel for transmitting data to a Remote Place using Bluetooth Classic
*/

// Setting libraries
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <driver/adc.h>
#include <esp_a2dp_api.h>
#include <esp_bt_main.h>
#include <esp_bt_device.h>

#define MIC_ADC_CHANNEL ADC1_CHANNEL_0  // GPIO36 if ADC1
#define SAMPLE_RATE 8000                // 8kHz sample rate
#define QUEUE_SIZE 20

// Implementing the Queue operations
QueueHandle_t adc_to_dsp_queue;
QueueHandle_t dsp_to_bluetooth_queue;

// Function prototypes
void setup_adc();
int read_audio_sample();
int process_audio(int sample);
void setup_bluetooth();
void send_audio_via_bluetooth(int sample);

// Defining ADC operation on core 0
void adc_task(void *pvParameters) {
    setup_adc();
    while (1) {
        int sample = read_audio_sample();
        if (xQueueSend(adc_to_dsp_queue, &sample, portMAX_DELAY) != pdPASS) {
            // Handle queue full error
            printf("ADC Queue full!\n");
        }
        vTaskDelay(pdMS_TO_TICKS(1000/SAMPLE_RATE));
    }
}

// Defining DSP operation on core 1
void dsp_task(void *pvParameters) {
    int sample;
    while (1) {
        if (xQueueReceive(adc_to_dsp_queue, &sample, portMAX_DELAY) == pdPASS) {
            int processed_sample = process_audio(sample);
            if (xQueueSend(dsp_to_bluetooth_queue, &processed_sample, portMAX_DELAY) != pdPASS) {
                // Handle queue full error
                printf("DSP Queue full!\n");
            }
        }
    }
}

// Defining Bluetooth operation on core 1
void bluetooth_task(void *pvParameters) {
    setup_bluetooth();
    int processed_sample;
    while (1) {
        if (xQueueReceive(dsp_to_bluetooth_queue, &processed_sample, portMAX_DELAY) == pdPASS) {
            send_audio_via_bluetooth(processed_sample);
        }
    }
}

// Creating Tasks and Pinning them to the cores
void app_main() {
    adc_to_dsp_queue = xQueueCreate(QUEUE_SIZE, sizeof(int));
    dsp_to_bluetooth_queue = xQueueCreate(QUEUE_SIZE, sizeof(int));

    if (!adc_to_dsp_queue || !dsp_to_bluetooth_queue) {
        printf("Error creating queues\n");
        return;
    }

    // ESP32 has two cores: 0 and 1
    xTaskCreatePinnedToCore(adc_task, "ADC_Task", 4096, NULL, configMAX_PRIORITIES-1, NULL, 0); // Core 0
    xTaskCreatePinnedToCore(dsp_task, "DSP_Task", 4096, NULL, configMAX_PRIORITIES-2, NULL, 1); // Core 1
    xTaskCreatePinnedToCore(bluetooth_task, "Bluetooth_Task", 4096, NULL, configMAX_PRIORITIES-2, NULL, 1); // Core 1
}

void setup_adc() {
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(MIC_ADC_CHANNEL, ADC_ATTEN_DB_11);
}

int read_audio_sample() {
    return adc1_get_raw(MIC_ADC_CHANNEL);
}

int process_audio(int sample) {
    // Simple processing - can be replaced with actual DSP algorithms
    // For example: apply gain, filtering, etc.
    return sample * 1.5;  // Just a simple gain for demonstration
}

void setup_bluetooth() {
    // Initialize Bluetooth controller
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    if (esp_bt_controller_init(&bt_cfg) != ESP_OK) {
        printf("Bluetooth controller init failed\n");
        return;
    }
    
    if (esp_bt_controller_enable(ESP_BT_MODE_CLASSIC_BT) != ESP_OK) {
        printf("Bluetooth controller enable failed\n");
        return;
    }
    
    if (esp_bluedroid_init() != ESP_OK) {
        printf("Bluedroid init failed\n");
        return;
    }
    
    if (esp_bluedroid_enable() != ESP_OK) {
        printf("Bluedroid enable failed\n");
        return;
    }
    
    // Set up A2DP sink (for audio streaming)
    esp_a2d_sink_init();
    esp_a2d_sink_register_data_callback(bluetooth_data_callback);
    
    // Make device discoverable
    esp_bt_gap_set_scan_mode(ESP_BT_SCAN_MODE_CONNECTABLE_DISCOVERABLE);
}

void send_audio_via_bluetooth(int sample) {
    // This would typically send data via A2DP
    // In a real implementation, you'd buffer samples and send packets
    // For demonstration, we just print the sample
    printf("Sending sample: %d\n", sample);
}

// Bluetooth data callback (would be implemented for A2DP)
void bluetooth_data_callback(const uint8_t *data, uint32_t len) {
    // Handle incoming Bluetooth data if needed
}







***************************************************************
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
    
    xTaskCreatePinnedToCore(adcSamplingTask, "ADC Sampling", 4096, NULL, 1, &Task1, 0);
    xTaskCreatePinnedToCore(bluetoothTask, "Bluetooth Tx", 4096, NULL, 1, &Task2, 1);
}

void loop() {
    // Nothing here, tasks handle everything
}
