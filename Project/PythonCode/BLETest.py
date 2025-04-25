import asyncio
import numpy as np
import soundfile as sf
from datetime import datetime
import os
import sys
import time

# Critical Windows configuration - MUST come first
if sys.platform == 'win32':
    import pythoncom
    pythoncom.CoInitialize()  # Initialize COM for this thread
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure TensorFlow before imports
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN warnings
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Disable GPU
os.environ['TF_NUM_INTEROP_THREADS'] = '1'  # Limit threads
os.environ['TF_NUM_INTRAOP_THREADS'] = '1'

# Now import TensorFlow
import tensorflow as tf
from tensorflow.keras.models import load_model

# Import Bleak after TensorFlow
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

# Configuration
TARGET_NAME = "ESP32_ML_PROJECT"
SERVICE_UUID = "63661bda-e38c-4eb0-9389-12523579b526"
CHAR_UUID = "8fd0a2f0-e842-492b-8d9c-213e28678075"
SAMPLE_RATE = 22050
RECORD_SECONDS = 15
MODEL_PATH = r"C:\Users\Jiary\Documents\GitHub\ML\Project\Model\respiratory_cnn_model.h5"
MIN_CONFIDENCE = 0.7
PASSKEY = 123456 

class_labels = ["Healthy", "COPD", "URTI", "Bronchiectasis", "Pneumonia", "Bronchiolitis"]

class BLERecorder:
    def __init__(self):
        self.audio_data = []
        self.model = self.load_model()
        
    def load_model(self):
        """Load model with thread isolation"""
        try:
            # Explicitly limit TensorFlow threads
            tf.config.threading.set_inter_op_parallelism_threads(1)
            tf.config.threading.set_intra_op_parallelism_threads(1)
            
            model = load_model(MODEL_PATH, compile=False)
            print("✅ Model loaded successfully")
            return model
        except Exception as e:
            print(f"❌ Model load failed: {e}")
            sys.exit(1)
            
    async def ble_operations(self):
        """Handle all BLE operations in isolated function"""
        print("🔍 Scanning for device...")
        device = await BleakScanner.find_device_by_name(TARGET_NAME, timeout=15.0)
        if not device:
            raise BleakError("Device not found")

        async with BleakClient(device.address) as client:
            print("🔐 Connected, starting stream...")
            await client.start_notify(CHAR_UUID, self.notification_handler)
            
            start_time = time.time()
            while (time.time() - start_time) < RECORD_SECONDS:
                await asyncio.sleep(0.1)
                
            await client.stop_notify(CHAR_UUID)
            print(f"✅ Collected {len(self.audio_data)} samples")

    def notification_handler(self, sender, data):
        """Handle incoming BLE data"""
        try:
            samples = np.frombuffer(data, dtype=np.int16)
            self.audio_data.extend(samples)
            print(f"📥 Received {len(samples)} samples")
        except Exception as e:
            print(f"⚠️ Data error: {e}")

    def predict_condition(self):
        """Run model prediction"""
        if len(self.audio_data) < SAMPLE_RATE:
            return None
            
        try:
            # Normalize audio
            audio_norm = np.array(self.audio_data) / 32768.0
            # Add your model-specific preprocessing here
            prediction = self.model.predict(np.expand_dims(audio_norm, axis=[0, -1]), verbose=0)
            pred_idx = np.argmax(prediction)
            confidence = prediction[0][pred_idx]
            
            if confidence >= MIN_CONFIDENCE:
                return class_labels[pred_idx], float(confidence)
            return None
        except Exception as e:
            print(f"⚠️ Prediction failed: {e}")
            return None

    def save_recording(self, condition=None):
        """Save WAV file with timestamp"""
        filename = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{condition}.wav" if condition else f"{filename}.wav"
        sf.write(filename, np.array(self.audio_data), SAMPLE_RATE)
        return filename

    async def run(self):
        """Main execution flow"""
        print("🆕 Starting new session...")
        self.audio_data = []
        
        try:
            # Run BLE operations
            await self.ble_operations()
            
            if len(self.audio_data) > 0:
                # Predict and save
                prediction = self.predict_condition()
                condition = prediction[0] if prediction else "Unknown"
                filename = self.save_recording(condition)
                
                print(f"💾 Saved as {filename}")
                if prediction:
                    print(f"🩺 Diagnosis: {prediction[0]} ({prediction[1]:.2%} confidence)")
            else:
                print("❌ No data received")

        except Exception as e:
            print(f"⚠️ Session error: {e}")

if __name__ == "__main__":
    # Set up recording directory
    os.makedirs("Recordings", exist_ok=True)
    os.chdir("Recordings")
    
    # Initialize and run
    recorder = BLERecorder()
    
    try:
        asyncio.run(recorder.run())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"🔥 Fatal error: {e}")
    finally:
        # Clean up COM initialization on Windows
        if sys.platform == 'win32':
            pythoncom.CoUninitialize()