import numpy as np
import librosa
import time
import os
import shutil
import wave
import tensorflow.lite as tflite
import soundfile as sf
import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from bleak import BleakClient
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

# Constants
DEVICE_ADDRESS = "10:06:1c:f4:7e:1e"  #MAC Address
BLE_SERVICE_UUID = "63661bda-e38c-4eb0-9389-12523579b526"
BLE_CHAR_UUID = "8fd0a2f0-e842-492b-8d9c-213e28678075"
DEVICE_NAME=  "ESP32_BT_ML_PROJECT"
SAMPLE_RATE = 22050 #Hz
N_MELS = 128  # Example: Number of Mel bands used during training
FEATURE_SIZE = 3840  # Must match model input shape
DURATION = 15  # Seconds to record
CHUNK_SIZE=20
MODEL_PATH = r"C:\Users\Jiary\Documents\GitHub\ML\Project\respiratory_cnn_model.lite"
MIN_CONFIDENCE = 0.7  # Minimum confidence for a valid prediction

esp32_address = "10:06:1c:f4:7e:1e"

async def test_ble_connection():
    print("Scanning...")
    device = await BleakScanner.find_device_by_address(esp32_address, timeout=10.0)
    if not device:
        print("Device not found.")
        return

    print("Found device. Connecting...")
    client = BleakClient(esp32_address)
    await client.connect()
    if client.is_connected:
        print("Connected successfully!")
    await client.disconnect()

asyncio.run(test_ble_connection())

class_labels = ["Healthy", "COPD", "URTI", "Bronchiectasis", "Pneumonia", "Bronchiolitis"]

# Load TFLite model
try:
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    print(f"Loaded TFLite model from {MODEL_PATH}")
except Exception as e:
    print(f"Error loading TFLite model: {e}")
    exit()


# Get model input/output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()



class AudioRecorder:
    def __init__(self):
        self.audio_data = []
        self.start_time = None
        
    async def notification_handler(self, sender, data):
        samples = np.frombuffer(data, dtype=np.int16)
        self.audio_data.extend(samples)
        
        # Print progress every second
        elapsed = time.time() - self.start_time
        if int(elapsed) != int(elapsed - 0.1):  # Update once per second
            print(f"Recording: {elapsed:.1f}s | Samples: {len(self.audio_data)}")

    async def record_audio(self):
        print(f"Starting {DURATION}-second recording...")
        self.audio_data = []
        self.start_time = time.time()
        
        async with BleakClient(DEVICE_ADDRESS) as client:
            await client.start_notify(CHARACTERISTIC_UUID, self.notification_handler)
            
            while (time.time() - self.start_time) < DURATION:
                await asyncio.sleep(0.1)  # Check every 100ms
            
            await client.stop_notify(CHARACTERISTIC_UUID)
        
        # Convert to numpy array and save
        audio_array = np.array(self.audio_data, dtype=np.int16)
        print(f"Recording complete! Total samples: {len(audio_array)}")
        
        # Save as WAV file
        filename = f"ble_recording_{int(time.time())}.wav"
        sf.write(filename, audio_array, SAMPLE_RATE)
        print(f"Saved as {filename}")


def extract_features(audio_data, sample_rate):
    """Extracts a Mel spectrogram and reshapes it to match model input."""
    # Convert to float32 and normalize to [-1, 1]
    audio_data = audio_data.astype(np.float32) / np.iinfo(np.int16).max

    # Compute Mel spectrogram
    spectrogram = librosa.feature.melspectrogram(y=audio_data, sr=sample_rate, n_mels=N_MELS)
    spectrogram = librosa.power_to_db(spectrogram, ref=np.max)  # Convert to dB scale

    # Normalize to [0, 1] (important for TFLite model) - Use training data min/max if possible
    # Example: Assuming you know the min/max from training:
    train_min = -80.0  # Replace with your actual training min
    train_max = 0.0   # Replace with your actual training max
    spectrogram = (spectrogram - train_min) / (train_max - train_min)
    spectrogram = np.clip(spectrogram, 0, 1) # Clip values to be within [0,1]

    # Flatten to 1D feature vector
    spectrogram = spectrogram.flatten()
    print(f"Spectrogram Shape: {spectrogram.shape}")  # (n_mels, time_frames)
    print(f"Number of Features: {spectrogram.size}")

    # Ensure it has exactly FEATURE_SIZE elements
    if len(spectrogram) != FEATURE_SIZE:
        print(f"Warning: Spectrogram size ({len(spectrogram)}) does not match expected size ({FEATURE_SIZE}).")
        if len(spectrogram) > FEATURE_SIZE:
            spectrogram = spectrogram[:FEATURE_SIZE]  # Trim
        else:
            spectrogram = np.pad(spectrogram, (0, FEATURE_SIZE - len(spectrogram)), mode='constant')  # Pad

    # Reshape to match TFLite input (1, 3840)
    return np.expand_dims(spectrogram, axis=0).astype(np.float32)




async def classify_audio():
    """Records audio, extracts features, and runs inference."""
    recorder= AudioRecorder(DEVICE_ADDRESS, BLE_CHAR_UUID, DURATION, SAMPLE_RATE)
    audio_data = await recorder.record_audio_from_ble()
    if audio_data is None or len(audio_data) == 0:
        print("No audio data received.")
        return

    # Prepare WAV file
    filename = f"recorded_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    wav_file = wave.open(filename, "wb")
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit audio (same as ESP32 ADC output)
    wav_file.setframerate(SAMPLE_RATE)
    wav_file.writeframes(audio_data.tobytes())
    print(f"Recording saved as {filename}")

    spectrogram = extract_features(audio_data, SAMPLE_RATE)

    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], spectrogram)
    interpreter.invoke()
    # Get output tensor
    output_data = interpreter.get_tensor(output_details[0]['index'])
    # Get predicted label
    predicted_label = np.argmax(output_data)  # Get class with highest confidence
    confidence = output_data[0][predicted_label]  # Confidence score

    if confidence >= MIN_CONFIDENCE:
        print(f"Prediction: {class_labels[predicted_label]} (Confidence: {confidence:.2f})")
    else:
        print(f"Prediction: Unknown (Confidence: {confidence:.2f} below threshold)")
    print(f"Raw model output: {output_data}")

if __name__ == "__main__":
    asyncio.run(classify_audio())

