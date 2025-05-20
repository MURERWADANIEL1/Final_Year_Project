#define MIC_PIN A0;  // Pin connected to the microphone

void setup() {
  Serial.begin(115200);  // Fast serial for plotting

  // Set ADC prescaler to 32: 16 MHz / 32 = 500 kHz
  ADCSRA = (ADCSRA & 0b11111000) | 0x05;  // Prescaler = 32
}

void loop() {
  int raw = analogRead(MIC_PIN);     // Takes ~25-30 µs now
  int signal = raw - 512;            // Remove DC bias

  // Send to Serial Plotter
  Serial.print("signal:");
  Serial.println(signal);

  // Optional: Lock y-axis
  Serial.println("min:-150");
  Serial.println("max:150");

  // Delay to maintain ~10 kHz total sampling rate
  // It is unknown how much time it takes to write to Serial Monitor
  // Feel free to comment out the delay line
  delayMicroseconds(44);  // 100 µs total per sample
}
