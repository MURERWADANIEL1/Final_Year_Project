#include "BluetoothSerial.h"
BluetoothSerial SerialBT;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  SerialBT.begin("ESP32 Audio");
  Serial.println("Bluetooth Device is Ready to Pair");
  
}

void loop() {
  // put your main code here, to run repeatedly:
  if (SerialBT.available()){
    char receivedChar=SerialBT.read();
    Serial.write(receivedChar);//echo for testing
    
  }
 // if (capture_audio_data()){
    //convert to suitable format
 //   SerialBT.write(audio_data, sizeof(audio_data));
  //}

}
