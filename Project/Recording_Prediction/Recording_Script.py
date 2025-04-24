import numpy as np
import librosa
import time
import os
import wave
import tensorflow.lite as tflite
import soundfile as sf
import asyncio
import sys
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError
from datetime import datetime

# Constants
DEVICE_NAME = "ESP32_ML_PROJECT"
BLE_SERVICE_UUID = "63661bda-e38c-4eb0-9389-12523579b526"
BLE_CHAR_UUID = "8fd0a2f0-e842-492b-8d9c-213e28678075"
SAMPLE_RATE = 22050  # Hz
N_MELS = 128
FEATURE_SIZE = 3840
DURATION = 15  # Seconds to record
MODEL_PATH = r"C:\Users\Jiary\Documents\GitHub\ML\Project\Model/respiratory_cnn_model.lite"
MIN_CONFIDENCE = 0.7  # Minimum confidence for valid prediction



class_labels = ["Healthy", "COPD", "URTI", "Bronchiectasis", "Pneumonia", "Bronchiolitis"]



class AudioRecorder:

    def __init__(self, device_name, ble_char_uuid, duration, sample_rate):

        self.device_name = device_name

        self.ble_char_uuid = ble_char_uuid

        self.duration = duration

        self.sample_rate = sample_rate

        self.audio_data = []

        self.start_time = None

        self.client = None

        self.connected = False



    def handle_disconnect(self, client):

        print("âš ï¸ Device disconnected!")

        self.connected = False

        # Attempt to reconnect automatically

        asyncio.create_task(self.ensure_connection())



    async def ensure_connection(self, timeout=10.0):

        if self.connected:

            return True

            

        print("Attempting to connect...")

        try:

            device= await BleakScanner.find_device_by_name(self.device_name, timeout=timeout)

            if not device:

                raise BleakDeviceNotFoundError(f"Device '{self.device_name}' not found")

            self.client = BleakClient(device,  

            disconnected_callback=self.handle_disconnect

            )

            await self.client.connect(timeout=timeout)

            self.connected = self.client.is_connected

            if self.connected:

                print("? Connected successfully")

            return self.connected

        except Exception as e:

            print(f"Connection failed: {e}")

            return False



    async def notification_handler(self, sender, data):

        try:

            samples = np.frombuffer(data, dtype=np.int16)

            self.audio_data.extend(samples)

            

            elapsed = time.time() - self.start_time

            if int(elapsed) != int(elapsed - 0.1):  # Update once per second

                print(f"Recording: {elapsed:.1f}s | Samples: {len(self.audio_data)}")

        except Exception as e:

            print(f"Error in notification handler: {e}")



    async def record_audio_from_ble(self):

        print(f"Starting {self.duration}-second recording...")

        self.audio_data = []

        self.start_time = time.time()



        try:

            if not await self.ensure_connection():

                raise Exception("Could not establish BLE connection")



            await self.client.start_notify(self.ble_char_uuid, self.notification_handler)

            

            # Main recording loop

            while (time.time() - self.start_time) < self.duration:

                if not self.connected:

                    raise Exception("Connection lost during recording")

                await asyncio.sleep(0.1)

            

            await self.client.stop_notify(self.ble_char_uuid)

            

            if not self.audio_data:

                raise Exception("No audio data received")

                

            audio_array = np.array(self.audio_data, dtype=np.int16)

            print(f"Recording complete! Total samples: {len(audio_array)}")

            

            # Save as WAV file

            filename = f"ble_recording_{int(time.time())}.wav"

            sf.write(filename, audio_array, self.sample_rate)

            print(f"Saved as {filename}")

            

            return audio_array

            

        except Exception as e:

            print(f"âš ï¸ Recording error: {e}")

            raise

        finally:

            if self.client and self.connected:

                await self.client.stop_notify(self.ble_char_uuid)

                await self.client.disconnect()

                self.connected = False



def extract_features(audio_data, sample_rate):

    """Extracts Mel spectrogram and reshapes for model input."""

    if len(audio_data) == 0:

        raise ValueError("Empty audio data received")

    

    # Convert and normalize audio

    audio_data = audio_data.astype(np.float32) / np.iinfo(np.int16).max



    # Compute Mel spectrogram

    spectrogram = librosa.feature.melspectrogram(

        y=audio_data, 

        sr=sample_rate, 

        n_mels=N_MELS

    )

    spectrogram = librosa.power_to_db(spectrogram, ref=np.max)



    # Normalize to [0, 1] using training min/max

    train_min, train_max = -80.0, 0.0

    spectrogram = (spectrogram - train_min) / (train_max - train_min)

    spectrogram = np.clip(spectrogram, 0, 1)



    # Flatten and ensure correct size

    spectrogram = spectrogram.flatten()

    if len(spectrogram) > FEATURE_SIZE:

        spectrogram = spectrogram[:FEATURE_SIZE]

    else:

        spectrogram = np.pad(

            spectrogram, 

            (0, FEATURE_SIZE - len(spectrogram)), 

            mode='constant'

        )



    return np.expand_dims(spectrogram, axis=0).astype(np.float32)



async def classify_audio():

    """Main function to record and classify audio."""

    try:

        # Initialize TFLite model

        interpreter = tflite.Interpreter(model_path=MODEL_PATH)

        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()

        output_details = interpreter.get_output_details()

        print(f"Loaded TFLite model from {MODEL_PATH}")



        # Record audio

        recorder = AudioRecorder(DEVICE_ADDRESS, BLE_CHAR_UUID, DURATION, SAMPLE_RATE)

        audio_data = await recorder.record_audio_from_ble()



        # Extract features and predict

        spectrogram = extract_features(audio_data, SAMPLE_RATE)

        interpreter.set_tensor(input_details[0]['index'], spectrogram)

        interpreter.invoke()

        output_data = interpreter.get_tensor(output_details[0]['index'])

        

        # Process results

        predicted_label = np.argmax(output_data)

        confidence = output_data[0][predicted_label]

        

        if confidence >= MIN_CONFIDENCE:

            print(f"Prediction: {class_labels[predicted_label]} (Confidence: {confidence:.2f})")

        else:

            print(f"Prediction: Unknown (Confidence: {confidence:.2f} below threshold)")

            

    except Exception as e:

        print(f"âš ï¸ Classification error: {e}")



async def test_ble_connection():

    """Test BLE connection before main recording."""

    print("Testing BLE connection...")

    try:

        device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)

        if not device:

            raise BleakDeviceNotFoundError(f"Device {DEVICE_NAME} not found")

            

        async with BleakClient(device) as client:

            if client.is_connected:

                print("âœ… Connection test successful")

            else:

                raise Exception("Failed to connect")

    except Exception as e:

        print(f"âš ï¸ Connection test failed: {e}")

        raise



if __name__ == "__main__":

    try:

        # First test the connection

        asyncio.run(test_ble_connection())

        # Then run the main classification

        asyncio.run(classify_audio())

    except KeyboardInterrupt:

        print("Script interrupted by user")

    except Exception as e:

        print(f"âš ï¸ Fatal error: {e}")

