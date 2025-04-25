import asyncio
import numpy as np
import soundfile as sf
from datetime import datetime
import os
import json
import time

class BLERecorder:
    def __init__(self):
        self.audio_data = []
        
    async def record_from_ble(self, target_name, service_uuid, char_uuid, record_seconds=15):
        """Record audio from BLE device with enhanced connection info"""
        from bleak import BleakScanner, BleakClient
        from bleak.exc import BleakError

        print(f"\n Scanning for BLE device: {target_name}...")
        device = await BleakScanner.find_device_by_name(target_name, timeout=15.0)
        if not device:
            raise BleakError(f"Device {target_name} not found")

        print(f" Found Device:")
        print(f"   Name: {device.name}")
        print(f"   Address: {device.address}")

        async with BleakClient(device.address) as client:
            print("\n Connection Established:")
            print(f"   Device: {client.address}")
            print(f"   MTU Size: {client.mtu_size}")
            
            # Proper service count using list conversion
            service_count = len(list(client.services))
            print(f"   Services: {service_count} available")
            
            print("\nStarting audio stream...")
            await client.start_notify(char_uuid, self._notification_handler)
            
            start_time = time.time()
            while (time.time() - start_time) < record_seconds:
                await asyncio.sleep(0.1)
                
            await client.stop_notify(char_uuid)
            print(f"\nRecording Complete - Collected {len(self.audio_data)} samples")
            return self.audio_data

    def _notification_handler(self, sender, data):
        """Handle incoming BLE data"""
        try:
            samples = np.frombuffer(data, dtype=np.int16)
            self.audio_data.extend(samples.tolist())
            print(f"Received {len(samples)} samples (Total: {len(self.audio_data)})", end='\r')
        except Exception as e:
            print(f"\nData error: {e}")

    def save_recording(self, audio_data, sample_rate, condition=None):
        """Save recording with enhanced metadata"""
        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%b_%d_%H%M%S")
        filename = f"{timestamp}_{condition}.wav" if condition else f"{timestamp}.wav"
        
        audio_array = np.array(audio_data, dtype=np.int16)
        sf.write(filename, audio_array, sample_rate)
        
        # Create companion metadata file
        meta_filename = f"{timestamp}_meta.json"
        with open(meta_filename, "w") as f:
            json.dump({
                "original_file": filename,
                "sample_count": len(audio_data),
                "sample_rate": sample_rate,
                "duration_sec": len(audio_data)/sample_rate,
                "timestamp": now.isoformat(),
                "data_type": "int16"
            }, f, indent=2)
            
        return filename

if __name__ == "__main__":
    # Configuration
    TARGET_NAME = "ESP32_ML_PROJECT"
    SERVICE_UUID = "63661bda-e38c-4eb0-9389-12523579b526"
    CHAR_UUID = "8fd0a2f0-e842-492b-8d9c-213e28678075"
    SAMPLE_RATE = 22050
    RECORD_SECONDS = 15

    # Create output directory
    os.makedirs("Recordings", exist_ok=True)
    os.chdir("Recordings")

    # Record from BLE
    recorder = BLERecorder()
    try:
        print("\n" + "="*50)
        print(f"Starting BLE Recording Session")
        print(f"   Target: {TARGET_NAME}")
        print(f"   Duration: {RECORD_SECONDS} seconds")
        print("="*50 + "\n")
        
        audio_data = asyncio.run(recorder.record_from_ble(
            TARGET_NAME,
            SERVICE_UUID,
            CHAR_UUID,
            RECORD_SECONDS
        ))
        
        if audio_data:
            filename = recorder.save_recording(audio_data, SAMPLE_RATE)
            print(f"\nSaved Files:")
            print(f"   Audio: {filename}")
            print(f"   Metadata: {filename.replace('.wav', '_meta.json')}")
            
            # Save raw data for processing
            with open("latest_recording.json", "w") as f:
                json.dump({
                    "audio_data": audio_data,
                    "sample_rate": SAMPLE_RATE,
                    "timestamp": datetime.now().isoformat()
                }, f)
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\n" + "="*50)
        print("Session Complete")
        print("="*50)