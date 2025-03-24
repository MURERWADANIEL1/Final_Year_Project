import serial
import wave
import numpy as np

# Serial port where ESP32 is connected (adjust accordingly)
SERIAL_PORT = "COM6"  # Change to "/dev/ttyUSB0" for Linux/Mac
BAUD_RATE = 115200
SAMPLE_RATE = 22050
BUFFER_SIZE = 256  # Matches ESP32 buffer
DURATION = 15  # Seconds to record

# Open serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Prepare WAV file
filename = "recorded_audio.wav"
wav_file = wave.open(filename, "wb")
wav_file.setnchannels(1)  # Mono
wav_file.setsampwidth(2)  # 16-bit audio (same as ESP32 ADC output)
wav_file.setframerate(SAMPLE_RATE)

print(f"Recording {DURATION} seconds of audio...")

audio_data = []
num_samples = SAMPLE_RATE * DURATION

try:
    while len(audio_data) < num_samples:
        if ser.in_waiting >= BUFFER_SIZE * 2:  # Check for available data
            raw_bytes = ser.read(BUFFER_SIZE * 2)  # Read 16-bit samples
            samples = np.frombuffer(raw_bytes, dtype=np.int16)
            audio_data.extend(samples)

except KeyboardInterrupt:
    print("Recording stopped.")

# Convert list to numpy array
audio_data = np.array(audio_data[:num_samples], dtype=np.int16)

# Write to WAV file
wav_file.writeframes(audio_data.tobytes())
wav_file.close()

print(f"Recording saved as {filename}")

# Close serial connection
ser.close()
