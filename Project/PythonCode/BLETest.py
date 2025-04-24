import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import time
import numpy as np
import soundfile as sf
from datetime import datetime
import os

TARGET_NAME = "ESP32_ML_PROJECT"
SERVICE_UUID = "63661bda-e38c-4eb0-9389-12523579b526"
CHAR_UUID = "8fd0a2f0-e842-492b-8d9c-213e28678075"
SAMPLE_RATE = 22050
RECORD_SECONDS = 15
PASSKEY = 123456  
class BLERecorder:
    def __init__(self):
        self.audio_data = []        
    def notification_handler(self, sender, data):
        """Convert BLE packets to audio samples"""
        try:
            samples = np.frombuffer(data, dtype=np.int16)
            self.audio_data.extend(samples)
            print(f"Received {len(samples)} samples")
        except Exception as e:
            print(f"Data conversion error: {e}")
    def generate_filename(self):
        """Create unique filename with timestamp"""
        now = datetime.now()
        return now.strftime("%a_%H-%M-%S") + ".wav" 
    async def run(self):
        """Main recording session"""
        print("Starting new recording session")
        self.audio_data = []          
        try:
            print("Scanning for BLE device...")
            device = await BleakScanner.find_device_by_name(TARGET_NAME, timeout=15.0)
            if not device:
                raise BleakError(f"Device {TARGET_NAME} not found")
            print(f"Found {device.name} ({device.address})")
            async with BleakClient(device.address) as client:
                print("Attempting secure connection...")             
                try:
                    await client.pair()
                    print("Pairing successful")
                except Exception as e:
                    print(f"Pairing note: {str(e)}")
                print("Starting audio stream...")
                await client.start_notify(CHAR_UUID, self.notification_handler)                
                start_time = time.time()
                while (time.time() - start_time) < RECORD_SECONDS:
                    await asyncio.sleep(0.1)                      
                await client.stop_notify(CHAR_UUID)
                print(f"Collected {len(self.audio_data)} samples")
                # Save with unique filename
                filename = self.generate_filename()
                if len(self.audio_data) > 0:
                    sf.write(filename, np.array(self.audio_data), SAMPLE_RATE)
                    print(f"Saved as {filename}")
                else:
                    print("No audio data received")
        except Exception as e:
            print(f"Error: {e}")
if __name__ == "__main__":
    # Create output directory if needed
    os.makedirs("Recordings", exist_ok=True)
    os.chdir("Recordings")      
    recorder = BLERecorder()    
    try:
        asyncio.run(recorder.run())
    except KeyboardInterrupt:
        print("\nRecording stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")