#include <driver/adc.h>

#define DEFAULT_VREF 1100
esp_adc_cal_characteristics_t*adc_chars;


void setup() {
  // put your setup code here, to run once:
adc1_config_width(ADC_WIDTH_BIT_12);
adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_DB_11);
adc_chars=esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_11, ADC_WIDTH_BIT_12, DEFAULT_VREF, adc_chars);

}

void loop() {
  // put your main code here, to run repeatedly:

int sample=adc1_get_raw(ADC1_CHANNEL_0);
int milliVolts= esp_cal_raw_to_voltage(sample,adc_chars);
Serial.println(milliVolts);
}
